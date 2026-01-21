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
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from fastapi import Query

sys.path.insert(0, str(Path(__file__).parent))

from services.ai_service import ai_service
from services.scrapers import run_all_scrapers, search_youtube_comments, stream_youtube_comments
from database import supabase, get_products, add_product, get_reviews, get_dashboard_stats, get_product_by_id, delete_product

app = FastAPI(title="Sentiment Beacon API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProductCreate(BaseModel):
    name: str
    keywords: Optional[List[str]] = []
    track_reddit: Optional[bool] = False
    track_twitter: Optional[bool] = False
    track_youtube: Optional[bool] = True


class ScrapeTrigger(BaseModel):
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
        query = supabase.table("reviews").select("*")
        if product_id:
            query = query.eq("product_id", product_id)
        if platform:
            query = query.eq("platform", platform)
        resp = query.order("created_at", desc=True).limit(limit).execute()
        return {"success": True, "data": resp.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scrape/trigger")
async def api_scrape_trigger(payload: ScrapeTrigger):
    """Trigger scraping for a product_id. Runs YouTube scraper (and stubs for others) in parallel.

    Steps:
    - Fetch product and keywords
    - Run scrapers in parallel
    - Analyze fetched items with ai_service
    - Upsert into `reviews` table
    - Return count of new reviews
    """
    product_id = payload.product_id
    if not product_id:
        raise HTTPException(status_code=400, detail="product_id required")

    # Fetch product
    product = await get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    keywords = product.get("keywords") or []
    if not keywords:
        # default to product name
        keywords = [product.get("name")]

    # Run consolidated scrapers (YouTube + Reddit + Twitter) in parallel
    fetched_items = await run_all_scrapers(keywords, per_source=50)

    if not fetched_items:
        return {"success": True, "new": 0}

    # Analyze and prepare rows for insertion
    rows = []
    for it in fetched_items:
        content = it.get("content") or it.get("text") or ""
        # Run AI analysis in thread to avoid blocking (analyze_text is cached)
        analysis = await asyncio.to_thread(ai_service.analyze_text, content)
        row = {
            "product_id": product_id,
            "content": content,
            "platform": it.get("platform", "youtube"),
            "sentiment_score": float(analysis.get("score", 0.5)),
            "sentiment_label": analysis.get("label", "NEUTRAL"),
            "emotion": analysis.get("emotion", "neutral"),
            "credibility_score": float(analysis.get("credibility", it.get("credibility_score") or 0.5)),
            "source_url": it.get("source_url") or None,
            "created_at": it.get("created_at") or None,
        }
        rows.append(row)

    # Batch insert - ignore duplicates handling (Supabase upsert requires conflict key)
    try:
        insert_resp = supabase.table("reviews").insert(rows).execute()
        new_count = len(insert_resp.data) if insert_resp.data else 0
    except Exception as e:
        print(f"Insert error: {e}")
        new_count = 0

    return {"success": True, "new": new_count}


@app.post("/api/scrape/youtube")
async def api_scrape_youtube(payload: YoutubeScrapeRequest):
    url = (payload.url or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="url is required")

    max_results = payload.max_results or 50
    try:
        items = await search_youtube_comments(url, max_results=max_results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not items:
        return {"success": True, "saved": 0, "count": 0}

    saved_count = 0
    # If product_id provided, save to DB after analysis
    if payload.product_id:
        rows = []
        for it in items:
            content = it.get("content") or ""
            analysis = await asyncio.to_thread(ai_service.analyze_text, content)
            row = {
                "product_id": payload.product_id,
                "content": content,
                "platform": it.get("platform", "youtube"),
                "sentiment_score": float(analysis.get("score", 0.5)),
                "sentiment_label": analysis.get("label", "NEUTRAL"),
                "emotion": analysis.get("emotion", "neutral"),
                "credibility_score": float(analysis.get("credibility", it.get("credibility_score") or 0.5)),
                "source_url": it.get("source_url") or None,
                "created_at": it.get("created_at") or None,
            }
            rows.append(row)

        try:
            insert_resp = supabase.table("reviews").insert(rows).execute()
            saved_count = len(insert_resp.data) if insert_resp.data else 0
        except Exception as e:
            print(f"Insert error (youtube scrape): {e}")
            saved_count = 0

    return {"success": True, "saved": saved_count, "count": len(items)}


@app.get("/api/scrape/youtube/stream")
async def api_scrape_youtube_stream(url: str = Query(...), product_id: Optional[str] = Query(None), max_results: int = Query(50)):
    """Stream YouTube comments as Server-Sent Events (SSE).

    Each comment is yielded as a JSON `data` event. When complete, a final `done` event is sent.
    If `product_id` is provided, comments are inserted into `reviews` as they arrive and analyzed.
    """

    def event_generator():
        # Run the synchronous streamer in this thread
        for comment in stream_youtube_comments(url, max_results=max_results) or []:
            # Insert review if product_id provided
            if product_id:
                row = {
                    "product_id": product_id,
                    "content": comment.get("content") or "",
                    "platform": comment.get("platform", "youtube"),
                    "sentiment_score": None,
                    "sentiment_label": None,
                    "emotion": None,
                    "credibility_score": None,
                    "source_url": comment.get("source_url"),
                    "created_at": comment.get("created_at"),
                }
                try:
                    resp = supabase.table("reviews").insert(row).execute()
                    # Try to run analysis and save sentiment row as background
                    try:
                        analysis = ai_service.analyze_text(comment.get("content") or "")
                        # insert sentiment_analysis row
                        sent = {
                            "review_id": resp.data[0]["id"] if resp.data else None,
                            "product_id": product_id,
                            "label": analysis.get("label"),
                            "score": analysis.get("score"),
                            "emotions": analysis.get("emotion"),
                            "credibility": analysis.get("credibility"),
                            "aspects": analysis.get("aspects") or None,
                        }
                        if sent.get("review_id"):
                            supabase.table("sentiment_analysis").insert(sent).execute()
                    except Exception as e:
                        print(f"Background analysis error: {e}")
                except Exception as e:
                    print(f"Insert review error: {e}")

            # yield SSE formatted event
            try:
                import json
                payload = {"type": "comment", "comment": comment}
                yield "data: " + json.dumps(payload) + "\n\n"
            except Exception:
                continue

        # final done event
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/dashboard")
async def api_dashboard():
    # Use database helper which performs optimized queries and caching
    stats = await get_dashboard_stats()
    return {"success": True, "data": stats}


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

