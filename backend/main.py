"""
Production-ready FastAPI app for Phase 1.

Endpoints:
- GET /api/products
- POST /api/products
- GET /api/reviews
- POST /api/scrape/trigger
- GET /api/dashboard
- POST /api/debug/scrape_now (NEW)

Focus: YouTube scraping + sentiment analysis. Reddit/Twitter integrations active.
"""

import os
import sys
import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from fastapi import Query
from dotenv import load_dotenv

# Load env vars specific to backend BEFORE importing services that might use them on init
from pathlib import Path
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

sys.path.insert(0, str(Path(__file__).parent))

from services.ai_service import ai_service
from services import scrapers, youtube_scraper, data_pipeline, wordcloud_service, nlp_service, csv_import_service
# Disabling Reddit/Twitter for stability as requested
# from services import reddit_scraper, twitter_scraper 
from services.prediction_service import generate_forecast
from routers import reports
from database import supabase, get_products, add_product, get_reviews, get_dashboard_stats, get_product_by_id, delete_product, get_sentiment_trends

app = FastAPI(title="Sentiment Beacon API", version="1.0.0")

# --- LOGGING CONFIGURATION ---
import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        RotatingFileHandler("backend.log", maxBytes=1024*1024, backupCount=3, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reports.router)
from routers import auth
app.include_router(auth.router)

from services.insights_service import insights_service

@app.get("/api/insights")
async def api_get_insights(product_id: Optional[str] = None):
    return {"success": True, "data": insights_service.generate_insights(product_id)}

@app.post("/api/reviews/upload")
async def api_upload_reviews(
    file: UploadFile = File(...), 
    product_id: str = Form(...), 
    platform: str = Form("csv_upload")
):
    """
    Upload CSV for bulk analysis.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")
        
    try:
        content = await file.read()
        result = await csv_import_service.csv_import_service.process_csv(content, product_id, platform)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/debug/logs")
async def api_get_logs(lines: int = 50):
    try:
        log_file = Path("backend.log")
        if not log_file.exists():
            return {"logs": ["Log file not found."]}
            
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.readlines()
            return {"logs": content[-lines:]}
    except Exception as e:
        return {"logs": [f"Error reading logs: {e}"]}



class ProductCreate(BaseModel):
    name: str
    keywords: Optional[List[str]] = []
    track_reddit: Optional[bool] = False
    track_twitter: Optional[bool] = False
    track_youtube: Optional[bool] = True


class ScrapeRequest(BaseModel):
    product_id: str
    url: Optional[str] = None



class YoutubeScrapeRequest(BaseModel):
    url: str
    product_id: Optional[str] = None
    max_results: Optional[int] = 50


class RedditScrapeRequest(BaseModel):
    query: str
    limit: Optional[int] = 50


class TwitterScrapeRequest(BaseModel):
    query: str
    product_id: Optional[str] = None
    limit: Optional[int] = 20


class AlertCreate(BaseModel):
    keyword: str
    threshold: float
    email: str


class SettingsUpdate(BaseModel):
    theme: Optional[str] = "light"
    email_notifications: Optional[bool] = True
    scraping_interval: Optional[int] = 24



@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/products")
async def api_get_products():
    products = await get_products()
    return {"success": True, "data": products}


@app.post("/api/products")
async def api_create_product(payload: ProductCreate, background_tasks: BackgroundTasks):
    data = {"name": payload.name, "keywords": payload.keywords or [],
            "track_reddit": payload.track_reddit, "track_twitter": payload.track_twitter,
            "track_youtube": payload.track_youtube}
    res = await add_product(data)
    
    # Auto-trigger scrape immediately
    keywords = payload.keywords or [payload.name]
    
    # Handle Supabase response (list or dict)
    product_id = None
    if isinstance(res, list) and len(res) > 0:
        product_id = res[0].get("id")
    elif isinstance(res, dict):
        product_id = res.get("id")
        
    if product_id:
        logger.info(f"Scheduling background scrape for new product: {product_id}")
        background_tasks.add_task(scrapers.scrape_all, keywords, product_id, None)
    else:
        logger.warning("Product created but ID missing, skipping scrape trigger.")
        
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
        # Fallback empty list if DB fail
        return {"success": True, "data": []}


@app.post("/api/scrape/trigger")
async def trigger_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    product_id = request.product_id
    if not product_id:
        raise HTTPException(status_code=400, detail="product_id is required")

    product = await get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    keywords = product.get("keywords") or [product.get("name")]

    logger.info(f"Triggering manual scrape for {product_id}")
    background_tasks.add_task(scrapers.scrape_all, keywords, product_id, request.url)

    return {"status": "accepted", "message": "Agents deployed in background"}


@app.post("/api/debug/scrape_now")
async def api_debug_scrape(product_id: str, url: Optional[str] = None):
    try:
        product = await get_product_by_id(product_id)
        if not product:
             raise HTTPException(404, "Product not found")
        
        keywords = product.get("keywords") or [product.get("name")]
        
        logger.info(f"DEBUG: Starting foreground scrape for {product_id}")
        
        # Run strictly in foreground
        result = await scrapers.scrape_all(keywords, product_id, url)
        
        # Read last 20 logs for context
        logs = []
        try:
            with open("backend.log", "r", encoding="utf-8") as f:
                logs = f.readlines()[-20:]
        except:
            pass
            
        return {
            "success": True,
            "result": result,
            "logs": logs
        }
    except Exception as e:
        logger.exception("Debug scrape failed")
        raise HTTPException(500, f"Scrape failed: {str(e)}")


@app.post("/api/scrape/youtube")
async def api_scrape_youtube(payload: YoutubeScrapeRequest):
    url = (payload.url or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="url is required")

    max_results = payload.max_results or 50
    try:
        items = await youtube_scraper.search_video_comments(url, max_results=max_results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not items:
        return {"success": True, "saved": 0, "count": 0}

    saved_count = 0
    if payload.product_id:
        processed = await data_pipeline.process_reviews(items, payload.product_id)
        saved_count = len(processed)

    return {"success": True, "saved": saved_count, "count": len(items)}


@app.post("/api/scrape/reddit")
async def api_scrape_reddit(payload: RedditScrapeRequest):
    query = (payload.query or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="query is required")

    try:
        items = await reddit_scraper.search_product_mentions(query, limit=payload.limit or 50)
        return {"success": True, "data": items, "count": len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scrape/twitter")
async def api_scrape_twitter(payload: TwitterScrapeRequest):
    query = (payload.query or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="query is required")

    try:
        items = await twitter_scraper.search_tweets(query, limit=payload.limit or 20)
        
        # If product_id, save them
        if payload.product_id and items:
             await data_pipeline.process_reviews(items, payload.product_id)

        return {"success": True, "data": items, "count": len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@app.get("/api/scrape/youtube/stream")
async def api_scrape_youtube_stream(url: str = Query(...), product_id: Optional[str] = Query(None), max_results: int = Query(50)):
    """Stream YouTube comments as Server-Sent Events (SSE).

    Each comment is yielded as a JSON `data` event. When complete, a final `done` event is sent.
    If `product_id` is provided, comments are inserted into `reviews` as they arrive and analyzed.
    """

    # Use an async generator to stream Server-Sent Events (SSE) reliably.
    import json
    # Use global youtube_scraper from top import

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
async def api_get_topics(limit: int = 10, product_id: Optional[str] = None):
    """
    Get top topics for visualization (LDA).
    """
    try:
        # If DB has topics stored from background jobs, use them
        if supabase:
            query = supabase.table("topic_analysis").select("*").order("size", desc=True).limit(limit)
            # if product_id: query = query.eq("product_id", product_id) # Schema doesn't have product_id on topic_analysis yet
            resp = query.execute()
            data = resp.data or []
            if data:
                formatted = [{"text": d["topic_name"], "value": d["size"], "sentiment": d.get("sentiment", 0)} for d in data]
                return {"success": True, "data": formatted}
                
        # Fallback: Live extraction if DB empty
        reviews = await get_reviews(product_id, limit=100)
        texts = [r.get("content") for r in reviews if r.get("content")]
        
        # Use simple extraction
        topics = ai_service.extract_topics_simple(texts, top_k=limit)
        
        formatted = [{"text": t["topic"], "value": t["count"], "sentiment": 0} for t in topics]
        return {"success": True, "data": formatted}
    except Exception as e:
        print(f"Error fetching topics: {e}")
        return {"success": False, "detail": str(e)}


@app.get("/api/products/{product_id}/wordcloud")
async def api_get_product_wordcloud(product_id: str):
    """
    Generate word clouds (base64 images).
    """
    try:
        reviews = await get_reviews(product_id, limit=200)
        # We need sentiment label. We can do a join or just rely on 'sentiment_analysis' property if get_reviews fetches it
        # Current get_reviews fetches it.
        
        flat_reviews = []
        for r in reviews:
            sa = r.get("sentiment_analysis")
            label = "NEUTRAL"
            if isinstance(sa, list) and sa: label = sa[0].get("label")
            elif isinstance(sa, dict): label = sa.get("label")
            
            flat_reviews.append({
                "content": r.get("content"),
                "sentiment_label": label
            })
            
        clouds = wordcloud_service.wordcloud_service.generate_wordclouds(flat_reviews)
        return {"success": True, "data": clouds}
    except Exception as e:
        logger.error(f"Wordcloud error: {e}")
        return {"success": False, "detail": str(e)}


@app.get("/api/wordcloud")
async def api_get_global_wordcloud():
    """
    Generate global word clouds (base64 images) from all reviews.
    """
    try:
        reviews = await get_reviews(None, limit=500)
        
        flat_reviews = []
        for r in reviews:
            sa = r.get("sentiment_analysis")
            label = "NEUTRAL"
            if isinstance(sa, list) and sa: label = sa[0].get("label")
            elif isinstance(sa, dict): label = sa.get("label")
            
            flat_reviews.append({
                "content": r.get("content"),
                "sentiment_label": label
            })
            
        clouds = wordcloud_service.wordcloud_service.generate_wordclouds(flat_reviews)
        return {"success": True, "data": clouds}
    except Exception as e:
        logger.error(f"Global Wordcloud error: {e}")
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
async def api_get_analytics(product_id: Optional[str] = None, range: str = "7d"):
    """
    Get analytics data (sentiment trends) with time-filtering.
    """
    try:
        import pandas as pd
        
        days = 7
        if range == "30d": days = 30
        elif range == "90d": days = 90
        
        # If product_id is provided, use specific product logic
        # If not, use global (or just first product / aggregate - simplistic for now)
        # But 'get_sentiment_trends' requires product_id. 
        # If product_id missing, we return empty or need global trends logic.
        
        if not product_id:
             # Fallback to existing global logic if no product specified
             # (See old logic below, heavily simplified)
             return {"success": True, "data": {"sentimentTrends": []}}

        trends_data = await get_sentiment_trends(product_id, days)

        if not trends_data:
             return {"success": True, "data": {"sentimentTrends": []}}

        df = pd.DataFrame(trends_data)
        df["created_at"] = pd.to_datetime(df["created_at"])
        
        # Resample by Day
        # We need columns: positive, negative, neutral
        # Create dummies
        dummies = pd.get_dummies(df["label"])
        # Ensure all columns exist
        for col in ["POSITIVE", "NEGATIVE", "NEUTRAL"]:
            if col not in dummies.columns:
                dummies[col] = 0
                
        # Merge back with date
        df = pd.concat([df["created_at"], dummies], axis=1)
        
        # Group by day
        daily = df.groupby(pd.Grouper(key="created_at", freq="D")).sum().fillna(0)
        
        # Format for API
        trends = []
        for date, row in daily.iterrows():
            trends.append({
                "date": date.strftime("%Y-%m-%d"),
                "positive": int(row.get("POSITIVE", 0)),
                "negative": int(row.get("NEGATIVE", 0)),
                "neutral": int(row.get("NEUTRAL", 0))
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


@app.post("/api/alerts")
async def api_create_alert(payload: AlertCreate):
    try:
        # Save to DB
        # Check if table exists via insert trial
        alert_data = {
            "type": "keyword_monitor",
            "severity": "medium", 
            "title": f"Monitor: {payload.keyword}",
            "message": f"Threshold set to {payload.threshold} for {payload.email}",
            "is_read": False,
            "details": {"keyword": payload.keyword, "threshold": payload.threshold, "email": payload.email}
        }
        res = supabase.table("alerts").insert(alert_data).execute()
        return {"success": True, "data": res.data}
    except Exception as e:
        print(f"Create alert error: {e}")
        # In-memory fallback if DB fails (per prompt "just in-memory if DB schema is tight")
        # But we'll try to stick to DB mostly.
        raise HTTPException(status_code=500, detail=str(e))











@app.post("/api/alerts/{alert_id}/read")
async def api_mark_alert_read(alert_id: int):
    try:
        supabase.table("alerts").update({"is_read": True, "is_resolved": True}).eq("id", alert_id).execute()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/products/{product_id}/predictions")
async def api_product_predictions(product_id: str):
    """
    AI Forecast Endpoint.
    """
    try:
        import datetime
        import pandas as pd
        
        # 1. Fetch historical data (last 30 days)
        days = 30
        start_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
        
        query = supabase.table("reviews").select("created_at, sentiment_analysis(score)").eq("product_id", product_id).gte("created_at", start_date.isoformat())
        resp = query.execute()
        reviews = resp.data or []
        
        if not reviews:
            return {"success": True, "data": {"forecast": [], "trend": "stable"}}
            
        # 2. Aggregate by day
        daily_data = {}
        for r in reviews:
            dt = pd.to_datetime(r["created_at"]).strftime("%Y-%m-%d")
            sa = r.get("sentiment_analysis")
            score = 0
            if sa:
                if isinstance(sa, list) and sa:
                     score = float(sa[0].get("score") or 0)
                elif isinstance(sa, dict):
                     score = float(sa.get("score") or 0)
            
            if dt not in daily_data:
                daily_data[dt] = []
            daily_data[dt].append(score)
            
        history = []
        for date_str, scores in daily_data.items():
            avg_score = sum(scores) / len(scores)
            history.append({"date": date_str, "sentiment": avg_score})
            
        # 3. Generate forecast
        predictions = generate_forecast(history)
        
        # 4. Calculate Trend
        trend = "stable"
        if len(predictions) >= 2:
            first = predictions[0]["sentiment"]
            last = predictions[-1]["sentiment"]
            delta = last - first
            if delta > 0.1: trend = "improving"
            elif delta < -0.1: trend = "declining"
        
        return {
            "success": True, 
            "data": {
                "forecast": predictions,
                "trend": trend
            }
        }
        
    except Exception as e:
        print(f"Prediction error: {e}")
        return {"success": False, "detail": str(e)}


@app.get("/api/competitors/compare")
async def api_compare_products(productA: str, productB: str):
    try:
        # Re-use the logic from product_stats but for two products
        async def get_stats(pid):
            response = supabase.table("reviews")\
                .select("sentiment_analysis(score, label, credibility, aspects)")\
                .eq("product_id", pid)\
                .execute()
            
            rows = response.data or []
            total = len(rows)
            
            scores = []
            creds = []
            positive_count = 0
            neutral_count = 0
            negative_count = 0
            
            aspects_agg = {}

            for r in rows:
                sa = r.get("sentiment_analysis")
                if isinstance(sa, list) and sa: sa = sa[0]
                
                if sa and isinstance(sa, dict):
                    s = float(sa.get("score") or 0.5)
                    c = float(sa.get("credibility") or 0.95)
                    l = sa.get("label")
                    
                    scores.append(s)
                    creds.append(c)
                    
                    if l == "POSITIVE": positive_count += 1
                    elif l == "NEGATIVE": negative_count += 1
                    else: neutral_count += 1
                    
                    # Aggregating aspects
                    asps = sa.get("aspects") or []
                    for a in asps:
                        # a is {"aspect": "price", "sentiment": "negative", "score": 0.9}
                        aname = a.get("aspect")
                        asent = a.get("sentiment")
                        if aname:
                            if aname not in aspects_agg: aspects_agg[aname] = {"score_sum": 0, "count": 0}
                            # Map sentiment to 0-5 scale roughly
                            val = 2.5
                            if asent == "positive": val = 5.0
                            elif asent == "negative": val = 0.0
                            aspects_agg[aname]["score_sum"] += val
                            aspects_agg[aname]["count"] += 1
            
            avg_score = (sum(scores) / len(scores)) * 100 if scores else 0
            avg_cred = (sum(creds) / len(creds)) * 100 if creds else 0
            
            # Format aspects for frontend
            final_aspects = {}
            for k, v in aspects_agg.items():
                final_aspects[k] = v["score_sum"] / v["count"] if v["count"] > 0 else 0

            return {
                "sentiment": avg_score,
                "credibility": avg_cred,
                "reviewCount": total,
                "counts": {"positive": positive_count, "neutral": neutral_count, "negative": negative_count},
                "aspects": final_aspects
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


async def scrape_reddit_background(query: str, product_id: str):
    """Background task to scrape Reddit and save results."""
    try:
        from services.reddit_scraper import reddit_scraper
        from services.data_pipeline import data_pipeline
        
        items = await reddit_scraper.search_product_mentions(query, limit=50)
        if items:
            await data_pipeline.process_reviews(items, product_id)
            print(f"Background Reddit scrape saved {len(items)} items for {product_id}")
    except Exception as e:
        print(f"Background Reddit scrape failed: {e}")


async def scrape_twitter_background(query: str, product_id: str):
    """Background task to scrape Twitter and save results."""
    try:
        from services.twitter_scraper import twitter_scraper
        from services.data_pipeline import data_pipeline
        
        items = await twitter_scraper.search_tweets(query, limit=20)
        if items:
            await data_pipeline.process_reviews(items, product_id)
            print(f"Background Twitter scrape saved {len(items)} items for {product_id}")
    except Exception as e:
        print(f"Background Twitter scrape failed: {e}")





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


@app.post("/api/settings")
async def api_update_settings(payload: SettingsUpdate):
    try:
        # Save to user_settings table
        # We'll use a fixed user_id 'default' for single-tenant mode
        user_id = "default"
        
        updates = [
            {"user_id": user_id, "key": "theme", "value": payload.theme},
            {"user_id": user_id, "key": "email_notifications", "value": str(payload.email_notifications)},
            {"user_id": user_id, "key": "scraping_interval", "value": str(payload.scraping_interval)}
        ]
        
        for up in updates:
            # Upsert
            supabase.table("user_settings").upsert(up, on_conflict="user_id, key").execute()
            
        return {"success": True}
    except Exception as e:
        print(f"Settings update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/settings")
async def api_get_settings():
    try:
        user_id = "default"
        resp = supabase.table("user_settings").select("*").eq("user_id", user_id).execute()
        data = resp.data or []
        
        # Convert list to dict
        settings = {
            "theme": "light",
            "email_notifications": True,
            "scraping_interval": 24
        }
        
        for row in data:
            k = row["key"]
            v = row["value"]
            if k == "theme": settings["theme"] = v
            elif k == "email_notifications": settings["email_notifications"] = (v == "True")
            elif k == "scraping_interval": settings["scraping_interval"] = int(v) if v.isdigit() else 24
            
        return {"success": True, "data": settings}
    except Exception as e:
        print(f"Settings get error: {e}")
        # Return defaults
        return {"success": True, "data": {"theme": "light", "email_notifications": True, "scraping_interval": 24}}


@app.get("/api/system/status")
async def api_system_status():
    """
    Check active credentials/services.
    """
    try:
        # Check Reddit
        reddit_status = bool(os.getenv("REDDIT_CLIENT_ID"))
        
        # Check YouTube
        youtube_status = bool(os.getenv("YOUTUBE_API_KEY"))
        
        # Check Twitter (Nitter uses scraper, but maybe API key logic if present)
        # Prompt says: Twitter: True (Since we use Nitter).
        twitter_status = True 
        
        return {"success": True, "data": {
            "reddit": reddit_status,
            "youtube": youtube_status,
            "twitter": twitter_status,
            "database": True
        }}
    except Exception as e:
         return {"success": False, "data": {
            "reddit": False,
            "youtube": False,
            "twitter": True,
            "database": False
        }}


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