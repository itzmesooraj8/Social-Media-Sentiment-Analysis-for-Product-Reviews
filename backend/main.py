"""
Production-ready FastAPI app for Phase 1.

Endpoints:
- GET /api/products
- POST /api/products
- GET /api/reviews
- POST /api/scrape/trigger
- GET /api/dashboard

Focus: YouTube scraping + sentiment analysis. Reddit/Twitter are stubbed and deferred.
"""

import os
import sys
import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from fastapi import Query

sys.path.insert(0, str(Path(__file__).parent))

from services.ai_service import ai_service
from services import scrapers
from routers import reports
from database import supabase, get_products, add_product, get_reviews, get_dashboard_stats, get_product_by_id, delete_product

app = FastAPI(title="Sentiment Beacon API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reports.router)


class ProductCreate(BaseModel):
    name: str
    keywords: Optional[List[str]] = []
    track_reddit: Optional[bool] = False
    track_twitter: Optional[bool] = False
    track_youtube: Optional[bool] = True


class ScrapeRequest(BaseModel):
    product_id: str


class YoutubeScrapeRequest(BaseModel):
    url: str
    product_id: Optional[str] = None
    max_results: Optional[int] = 50


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/products")
async def api_get_products():
    products = await get_products()
    return {"success": True, "data": products}


@app.post("/api/products")
async def api_create_product(payload: ProductCreate):
    data = {"name": payload.name, "keywords": payload.keywords or [],
            "track_reddit": payload.track_reddit, "track_twitter": payload.track_twitter,
            "track_youtube": payload.track_youtube}
    res = await add_product(data)
    return {"success": True, "data": res}


@app.get("/api/reviews")
async def api_get_reviews(product_id: Optional[str] = None, platform: Optional[str] = None, limit: int = 100):
    try:
        # Join with sentiment_analysis to get scores/labels
        query = supabase.table("reviews").select("*, sentiment_analysis(*)")
        if product_id:
            query = query.eq("product_id", product_id)
        if platform:
            query = query.eq("platform", platform)
        resp = query.order("created_at", desc=True).limit(limit).execute()
        return {"success": True, "data": resp.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scrape/trigger")
async def trigger_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Non-blocking API Trigger.
    """
    product_id = request.product_id
    if not product_id:
        raise HTTPException(status_code=400, detail="product_id is required")

    product = await get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    keywords = product.get("keywords") or [product.get("name")]

    # Deploy agents in background
    background_tasks.add_task(scrapers.scrape_all, keywords, product_id)

    return {"status": "accepted", "message": "Agents deployed in background"}


@app.post("/api/scrape/youtube")
async def api_scrape_youtube(payload: YoutubeScrapeRequest):
    url = (payload.url or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="url is required")

    max_results = payload.max_results or 50
    try:
        # Assuming search_youtube_comments is still needed for direct URL scrapes
        from services.youtube_scraper import youtube_scraper
        items = await youtube_scraper.search_video_comments(url, max_results=max_results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not items:
        return {"success": True, "saved": 0, "count": 0}

    saved_count = 0
    if payload.product_id:
        # Re-using the data pipeline for consistency
        from services.data_pipeline import data_pipeline
        processed = await data_pipeline.process_reviews(items, payload.product_id)
        saved_count = len(processed)

    return {"success": True, "saved": saved_count, "count": len(items)}


@app.get("/api/scrape/youtube/stream")
async def api_scrape_youtube_stream(url: str = Query(...), product_id: Optional[str] = Query(None), max_results: int = Query(50)):
    """Stream YouTube comments as Server-Sent Events (SSE).

    Each comment is yielded as a JSON `data` event. When complete, a final `done` event is sent.
    If `product_id` is provided, comments are inserted into `reviews` as they arrive and analyzed.
    """

    # Use an async generator to stream Server-Sent Events (SSE) reliably.
    from services.youtube_scraper import youtube_scraper
    from services.data_pipeline import data_pipeline
    import json

    async def event_generator():
        try:
            # Stream comments using the async generator
            async for comment in youtube_scraper.search_video_comments_stream(url, max_results=max_results):
                try:
                    payload = {"type": "comment", "comment": comment}
                    yield "data: " + json.dumps(payload) + "\n\n"

                    # If a product_id is provided, process/save asynchronously
                    if product_id:
                        # fire-and-forget processing so streaming isn't blocked
                        asyncio.create_task(data_pipeline.process_reviews([comment], product_id))

                    # small pause to allow client-side rendering to stay responsive
                    await asyncio.sleep(0.01)
                except Exception:
                    # skip problematic comment but keep stream alive
                    continue

        except Exception as e:
            # stream an error event so client can surface it
            try:
                error_payload = {"error": str(e), "message": "An error occurred during the stream."}
                yield "event: error\ndata: " + json.dumps(error_payload) + "\n\n"
            except Exception:
                pass
        finally:
            # signal completion
            try:
                yield "event: done\ndata: {}\n\n"
            except Exception:
                return

    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive",
    }

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=headers)


@app.get("/api/dashboard")
async def api_dashboard():
    # Use database helper which performs optimized queries and caching
    stats = await get_dashboard_stats()
    return {"success": True, "data": stats}


@app.get("/api/topics")
async def api_get_topics(limit: int = 10):
    """
    Get top topics for visualization.
    """
    try:
        if supabase:
            resp = supabase.table("topic_analysis").select("*").order("size", desc=True).limit(limit).execute()
            data = resp.data or []
            # format for frontend
            formatted = [{"text": d["topic_name"], "value": d["size"], "sentiment": d.get("sentiment", 0)} for d in data]
            return {"success": True, "data": formatted}
        else:
            return {"success": True, "data": []}
    except Exception as e:
        print(f"Error fetching topics: {e}")
        return {"success": False, "detail": str(e)}


def _ensure_supabase_available():
    if supabase is None:
        raise HTTPException(status_code=500, detail="Supabase client not initialized. Check backend .env for SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")


class AnalyzeRequest(BaseModel):
    text: Optional[str]


@app.post("/api/analyze")
async def api_analyze(payload: AnalyzeRequest):
    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    try:
        # Run analysis in thread (model is CPU-bound)
        result = await asyncio.to_thread(ai_service.analyze_text, text)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/products/{product_id}")
async def api_delete_product(product_id: str):
    try:
        resp = await delete_product(product_id)
        return {"success": True, "data": resp}
    except HTTPException:
        raise
    except Exception as e:
        print(f"api_delete_product error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/products/{product_id}/stats")
async def api_product_stats(product_id: str):
    """
    Get stats for a specific product (for comparison/War Room).
    """
    try:
        if not supabase: 
            return {"success": False, "detail": "DB unavailable"}
        
        # Calc stats for specific product
        # 1. Count reviews
        reviews = supabase.table("reviews").select("id", count="exact").eq("product_id", product_id).execute()
        total = reviews.count or 0
        
        # 2. Aggregated sentiment
        # We assume sentiment_analysis is linked. 
        # A join would be better but simple separate queries are safer for now.
        sentiments = supabase.table("sentiment_analysis").select("score, label").eq("product_id", product_id).execute()
        data = sentiments.data or []
        
        avg_score = 0
        positive_count = 0
        if data:
            scores = [float(d.get("score", 0.5)) for d in data]
            avg_score = sum(scores) / len(scores)
            positive_count = sum(1 for d in data if d.get("label") == "POSITIVE")
            
        pos_percent = (positive_count / len(data)) * 100 if data else 0
        
        return {
            "success": True, 
            "data": {
                "total_reviews": total,
                "average_sentiment": avg_score,
                "positive_percent": round(pos_percent, 1)
            }
        }
    except Exception as e:
        print(f"Product stats error: {e}")
        return {"success": False, "detail": str(e)}


@app.get("/api/integrations")
async def api_get_integrations():
    # Simple stub for frontend: try to read 'integrations' table if present, otherwise return empty
    try:
        resp = supabase.table("integrations").select("*").execute()
        data = resp.data or []
    except Exception:
        data = []
    return {"success": True, "data": data}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

