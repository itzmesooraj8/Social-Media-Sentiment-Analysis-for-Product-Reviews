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


@app.get("/api/analytics")
async def api_get_analytics(range: str = "7d"):
    """
    Get analytics data for charts (daily sentiment, etc).
    """
    try:
        # 1. Daily Sentiment Trend (Last 7 days)
        # Using a raw SQL query for aggregation as Supabase JS client doesn't support complex group_by easily without RPC
        # But we can simulate it by fetching recent reviews and aggregating in python for simplicity if volume is low,
        # or better, use an RPC call if it existed.
        # For this sprint, we'll fetch reviews and aggregate in Python to ensure it works without migration.
        
        # Calculate start date based on range (default 7d)
        import datetime
        days = 7
        if range == "30d": days = 30
        start_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
        
        query = supabase.table("reviews").select("created_at, sentiment_analysis(label)").gte("created_at", start_date.isoformat())
        resp = query.execute()
        reviews = resp.data or []

        # Aggregate by date
        daily_stats = {}
        for r in reviews:
            date_str = r["created_at"].split("T")[0]
            if date_str not in daily_stats:
                daily_stats[date_str] = {"positive": 0, "negative": 0, "neutral": 0, "total": 0}
            
            # Extract label
            label = "NEUTRAL"
            if r.get("sentiment_analysis"):
                # Handle list or dict return from join
                sa = r["sentiment_analysis"]
                if isinstance(sa, list) and sa:
                    label = sa[0].get("label", "NEUTRAL")
                elif isinstance(sa, dict):
                    label = sa.get("label", "NEUTRAL")
            
            daily_stats[date_str]["total"] += 1
            if label == "POSITIVE":
                daily_stats[date_str]["positive"] += 1
            elif label == "NEGATIVE":
                daily_stats[date_str]["negative"] += 1
            else:
                daily_stats[date_str]["neutral"] += 1
        
        # Format for Recharts
        trends = []
        sorted_dates = sorted(daily_stats.keys())
        for d in sorted_dates:
            stats = daily_stats[d]
            trends.append({
                "date": d,
                "positive": stats["positive"],
                "negative": stats["negative"],
                "neutral": stats["neutral"]
            })
            
        return {"success": True, "data": {"sentimentTrends": trends}}

    except Exception as e:
        print(f"Analytics error: {e}")
        return {"success": False, "detail": str(e)}


@app.get("/api/alerts")
async def api_get_alerts(limit: int = 20):
    """
    Fetch live alerts.
    Priority: Critical/High first.
    """
    try:
        # Fetch from 'alerts' table if exists
        query = supabase.table("alerts").select("*").order("created_at", desc=True).limit(limit)
        resp = query.execute()
        return {"success": True, "data": resp.data or []}
    except Exception as e:
        # Fallback if table doesn't exist or error, return empty to avoid crash
        print(f"Alerts fetch error: {e}")
        return {"success": False, "data": []}


@app.post("/api/alerts/{alert_id}/read")
async def api_mark_alert_read(alert_id: int):
    try:
        supabase.table("alerts").update({"is_read": True, "is_resolved": True}).eq("id", alert_id).execute()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/competitors/compare")
async def api_compare_products(productA: str, productB: str):
    try:
        # Re-use the logic from product_stats but for two products
        async def get_stats(pid):
            reviews = supabase.table("reviews").select("id", count="exact").eq("product_id", pid).execute()
            total = reviews.count or 0
            
            sentiments = supabase.table("sentiment_analysis").select("score, label, credibility").eq("product_id", pid).execute()
            data = sentiments.data or []
            
            avg_score = 0
            avg_cred = 0
            positive_count = 0
            neutral_count = 0
            negative_count = 0
            
            if data:
                scores = [float(d.get("score", 0.5)) for d in data]
                creds = [float(d.get("credibility", 0.95)) for d in data] # default high cred if missing
                avg_score = (sum(scores) / len(scores)) * 100 # scale to 0-100
                avg_cred = (sum(creds) / len(creds)) * 100
                
                for d in data:
                    l = d.get("label")
                    if l == "POSITIVE": positive_count += 1
                    elif l == "NEGATIVE": negative_count += 1
                    else: neutral_count += 1
            
            return {
                "sentiment": avg_score,
                "credibility": avg_cred,
                "reviewCount": total,
                "counts": {"positive": positive_count, "neutral": neutral_count, "negative": negative_count}
            }
            
        statsA = await get_stats(productA)
        statsB = await get_stats(productB)
        
        return {
            "success": True, 
            "data": {
                "metrics": {
                    "productA": statsA,
                    "productB": statsB
                }
            }
        }
    except Exception as e:
        print(f"Compare error: {e}")
        return {"success": False, "detail": str(e)}


@app.get("/api/reports")
async def api_list_reports():
    import glob
    try:
        # List PDF files in reports directory
        report_dir = Path(__file__).parent / "reports"
        files = glob.glob(str(report_dir / "*.pdf"))
        
        reports_list = []
        for f in files:
            path = Path(f)
            stat = path.stat()
            reports_list.append({
                "id": path.stem,
                "filename": path.name,
                "created_at": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "size": stat.st_size
            })
            
        # Sort by newest
        reports_list.sort(key=lambda x: x["created_at"], reverse=True)
        return {"success": True, "data": reports_list}
    except Exception as e:
        return {"success": False, "detail": str(e)}


@app.get("/api/reports/{filename}")
async def api_download_report(filename: str):
    from fastapi.responses import FileResponse
    report_dir = Path(__file__).parent / "reports"
    file_path = report_dir / filename
    
    # Security check to prevent directory traversal
    if not file_path.resolve().is_relative_to(report_dir.resolve()):
         raise HTTPException(status_code=403, detail="Access denied")
         
    if not file_path.exists():
        # Try finding by ID (stem) if extension missing
        candidates = list(report_dir.glob(f"{filename}*"))
        if candidates:
            file_path = candidates[0]
        else:
            raise HTTPException(status_code=404, detail="Report not found")
            
    return FileResponse(file_path, media_type='application/pdf', filename=file_path.name)


@app.get("/api/system/status")
async def api_system_status():
    """
    Check active credentials/services.
    """
    # Simple check of env vars for this sprint
    status = {
        "reddit": bool(os.getenv("REDDIT_CLIENT_ID")),
        "twitter": bool(os.getenv("TWITTER_API_KEY")),
        "youtube": bool(os.getenv("YOUTUBE_API_KEY")),
        "database": True # Assumed if we are here
    }
    return {"success": True, "data": status}


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

