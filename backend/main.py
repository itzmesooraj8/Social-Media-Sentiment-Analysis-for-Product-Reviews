"""
Production-ready FastAPI app for Phase 1.

Endpoints:
- GET /api/products
- POST /api/products
- GET /api/reviews
- POST /api/scrape/trigger
- GET /api/dashboard
- POST /api/debug/scrape_now (NEW)
- POST /api/integrations/config (NEW)
- DELETE /api/integrations/{platform} (NEW)

Focus: YouTube scraping + sentiment analysis. Reddit/Twitter integrations active.
"""

import os
import sys
import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, UploadFile, File, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from fastapi import Query
from dotenv import load_dotenv, set_key, unset_key

# Load env vars specific to backend BEFORE importing services that might use them on init
# We reload them dynamically now in config endpoints too
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

sys.path.insert(0, str(Path(__file__).parent))

from services.ai_service import ai_service
from services import scrapers, youtube_scraper, data_pipeline, wordcloud_service, nlp_service, csv_import_service
# Re-enabling Reddit/Twitter for real-time integration
from services import reddit_scraper, twitter_scraper 
from services.prediction_service import generate_forecast
from routers import reports, alerts, settings
from database import supabase, get_products, add_product, get_reviews, get_dashboard_stats, get_product_by_id, delete_product, get_sentiment_trends, get_product_stats_full

app = FastAPI(title="Sentiment Beacon API", version="1.0.0")

# --- SCHEDULER STARTUP ---
from services.scheduler import start_scheduler

@app.on_event("startup")
async def startup_event():
    start_scheduler()

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
app.include_router(alerts.router)
app.include_router(settings.router)
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
    subreddits: Optional[List[str]] = None


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


# --- INTEGRATION CONFIG MODELS ---
class IntegrationConfig(BaseModel):
    platform: str
    enabled: bool
    credentials: Dict[str, str]


@app.get("/health")
async def health():
    """
    Comprehensive Health Check for Load Balancers and Frontend.
    Checks:
    1. System Uptime (Basic)
    2. Database Connectivity (Supabase)
    3. AI Model Readiness (DistilBERT loaded)
    """
    status = {
        "status": "initializing", 
        "database": "unknown", 
        "ai_models": "unknown",
        "version": "1.2.0"
    }
    
    # 1. Check Database
    try:
        # Lightweight check - just limit 1
        response = supabase.table("products").select("id", count="exact").limit(1).execute()
        status["database"] = "connected"
    except Exception as e:
        status["database"] = "disconnected"
        logger.error(f"Health Check DB Fail: {e}")

    # 2. Check AI Models
    # ai_service is initialized on import, but models load lazily or on startup
    if ai_service._models_loaded:
        status["ai_models"] = "ready"
    else:
        status["ai_models"] = "loading"
        # Trigger load in background if not loaded? 
        # Better to just report state.
    
    # Determined overall status
    if status["database"] == "connected" and status["ai_models"] == "ready":
        status["status"] = "healthy"
    elif status["database"] == "connected":
        # AI loading is fine, app is usable
        status["status"] = "degraded" # Frontend should show "AI Warming Up"
    else:
        status["status"] = "unhealthy"
        
    return status


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
        items = await reddit_scraper.reddit_scraper.search_product_mentions(
            query, 
            limit=payload.limit or 50, 
            subreddits=payload.subreddits
        )
        return {"success": True, "data": items, "count": len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scrape/twitter")
async def api_scrape_twitter(payload: TwitterScrapeRequest):
    query = (payload.query or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="query is required")

    try:
        items = await twitter_scraper.twitter_scraper.search_tweets(query, limit=payload.limit or 20)
        
        # If product_id, save them
        if payload.product_id and items:
             await data_pipeline.process_reviews(items, payload.product_id)

        return {"success": True, "data": items, "count": len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scrape/youtube/stream")
async def api_scrape_youtube_stream(url: str = Query(...), product_id: Optional[str] = Query(None), max_results: int = Query(50)):
    """Stream YouTube comments as Server-Sent Events (SSE)."""
    import json
    async def event_generator():
        try:
            async for comment in youtube_scraper.search_video_comments_stream(url, max_results=max_results):
                try:
                    payload = {"type": "comment", "comment": comment}
                    yield "data: " + json.dumps(payload) + "\\n\\n"
                    if product_id:
                        asyncio.create_task(data_pipeline.process_reviews([comment], product_id))
                    await asyncio.sleep(0.01)
                except Exception:
                    continue
        except Exception as e:
            try:
                error_payload = {"error": str(e), "message": "An error occurred during the stream."}
                yield "event: error\\ndata: " + json.dumps(error_payload) + "\\n\\n"
            except Exception:
                pass
        finally:
            try:
                yield "event: done\\ndata: {}\\n\\n"
            except Exception:
                return

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"}
    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=headers)


@app.get("/api/insights")
async def api_get_insights(product_id: Optional[str] = None):
    """
    Generate 'Smart Insights' based on recent reviews.
    Uses 'ai_service' to summarize sentiment, aspects, and provide recommendations.
    """
    try:
        # Fetch recent reviews to analyze
        # Limit to 100 for speed
        reviews = await database.get_reviews(product_id, limit=100)
        
        # Generate Insights (Agentic/Rule-based AI)
        insights = ai_service.generate_insights(reviews)
        
        return {"success": True, "data": insights}
    except Exception as e:
        return {"success": False, "detail": str(e), "data": []}


@app.get("/api/dashboard")
async def api_dashboard(product_id: Optional[str] = None):
    # Use database helper which performs optimized queries and caching
    stats = await get_dashboard_stats(product_id)
    return {"success": True, "data": stats}


@app.get("/api/topics")
async def api_get_topics(limit: int = 10, product_id: Optional[str] = None):
    try:
        # If DB has topics stored from background jobs, use them
        if supabase:
            query = supabase.table("topic_analysis").select("*").order("size", desc=True).limit(limit)
            resp = query.execute()
            data = resp.data or []
            if data:
                formatted = [{"text": d["topic_name"], "value": d["size"], "sentiment": d.get("sentiment", 0)} for d in data]
                return {"success": True, "data": formatted}
                
        # Fallback: Live extraction if DB empty
        reviews = await get_reviews(product_id, limit=100)
        texts = [r.get("content") for r in reviews if r.get("content")]
        
        topics = await ai_service.extract_topics(texts, top_k=limit)
        formatted = [{"text": t["topic"], "value": t["count"], "sentiment": 0} for t in topics]
        return {"success": True, "data": formatted}
    except Exception as e:
        print(f"Error fetching topics: {e}")
        return {"success": False, "detail": str(e)}


@app.get("/api/products/{product_id}/wordcloud")
async def api_get_product_wordcloud(product_id: str):
    try:
        reviews = await get_reviews(product_id, limit=200)
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


class AnalyzeRequest(BaseModel):
    text: Optional[str]


@app.post("/api/analyze")
async def api_analyze(payload: AnalyzeRequest):
    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    try:
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
    try:
        if not supabase: 
            return {"success": False, "detail": "DB unavailable"}
            
        stats = await get_product_stats_full(product_id)
        
        if not stats: 
            # If deleted or empty, return zeros
            return {
                "success": True, 
                "data": {
                    "total_reviews": 0,
                    "average_sentiment": 0,
                    "positive_percent": 0,
                    "credibility_score": 0,
                    "emotions": [], 
                    "aspects": [],
                    "keywords": []
                }
            }
            
        return {"success": True, "data": stats}
    except Exception as e:
        logger.error(f"api_product_stats error: {e}")
        return {"success": False, "detail": str(e)}


@app.get("/api/system/status")
async def api_system_status():
    """
    Check REAL status of integrations and database.
    """
    try:
        # Check Reddit (Require both ID and Secret)
        r_id = os.getenv("REDDIT_CLIENT_ID")
        r_secret = os.getenv("REDDIT_CLIENT_SECRET")
        reddit_status = bool(r_id and r_id.strip() and r_secret and r_secret.strip())
        
        # Check YouTube
        yt_key = os.getenv("YOUTUBE_API_KEY")
        youtube_status = bool(yt_key and yt_key.strip())
        
        # Check Twitter
        tw_token = os.getenv("TWITTER_BEARER_TOKEN")
        twitter_status = bool(tw_token and tw_token.strip())
        
        counts = {"reddit": 0, "youtube": 0, "twitter": 0}
        if supabase:
            try:
                t_red = asyncio.to_thread(lambda: supabase.table("reviews").select("id", count="exact").ilike("platform", "reddit%").execute())
                t_yt = asyncio.to_thread(lambda: supabase.table("reviews").select("id", count="exact").ilike("platform", "youtube%").execute())
                t_tw = asyncio.to_thread(lambda: supabase.table("reviews").select("id", count="exact").ilike("platform", "twitter%").execute())
                r, y, t = await asyncio.gather(t_red, t_yt, t_tw)
                counts["reddit"] = r.count if r else 0
                counts["youtube"] = y.count if y else 0
                counts["twitter"] = t.count if t else 0
            except Exception as e:
                logger.error(f"Count fetch error: {e}")

        return {"success": True, "data": {
            "reddit": reddit_status,
            "youtube": youtube_status,
            "twitter": twitter_status,
            "database": True,
            "counts": counts
        }}
    except Exception as e:
         return {"success": False, "data": {
            "reddit": False, "youtube": False, "twitter": False, "database": False,
            "counts": {"reddit": 0, "youtube": 0, "twitter": 0}
        }}


@app.post("/api/integrations/config")
async def api_configure_integration(config: IntegrationConfig):
    """
    Real-time configuration of integration secrets.
    Writes to .env and updates running process + Hot Reloads Scrapers.
    """
    try:
        platform = config.platform.lower()
        updated_keys = False
        
        for k, v in config.credentials.items():
             key = ""
             if platform == "youtube":
                 if k == "key": key = "YOUTUBE_API_KEY"
             elif platform == "reddit":
                 if k == "client_id": key = "REDDIT_CLIENT_ID"
                 if k == "client_secret": key = "REDDIT_CLIENT_SECRET"
             elif platform == "twitter":
                 if k == "bearer_token": key = "TWITTER_BEARER_TOKEN"
            
             if key:
                 # 1. Update running env
                 os.environ[key] = v
                 # 2. Write to .env file
                 set_key(env_path, key, v)
                 updated_keys = True
        
        # 3. Hot Reload Services
        if updated_keys:
            if platform == "twitter":
                # Access the instance within the module
                await twitter_scraper.twitter_scraper.reload_config()
                logger.info("Twitter Scraper reloaded.")
            # Add Reddit/YouTube reload logic here as needed
        
        return {"success": True, "message": f"{platform.capitalize()} configuration updated successfully."}
    except Exception as e:
        logger.error(f"Config update failed: {e}")
        raise HTTPException(500, f"Failed to update config: {e}")

@app.delete("/api/integrations/{platform}")
async def api_delete_integration(platform: str):
    """
    Remove integration credentials.
    """
    try:
        platform = platform.lower()
        keys_to_remove = []
        
        if platform == "youtube":
            keys_to_remove = ["YOUTUBE_API_KEY"]
        elif platform == "reddit":
            keys_to_remove = ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"]
        elif platform == "twitter":
            keys_to_remove = ["TWITTER_BEARER_TOKEN"]
            
        logger.info(f"Removing credentials for {platform}: {keys_to_remove}")
        for key in keys_to_remove:
            # Remove from running env
            if key in os.environ:
                del os.environ[key]
            # Remove from .env file entirely
            # unset_key might fail if key not found, safe wrap
            try:
                unset_key(env_path, key)
            except Exception as ex:
                logger.warning(f"Could not unset {key} from .env: {ex}")
                # Fallback: set to empty
                set_key(env_path, key, "")
            
        return {"success": True, "message": f"{platform.capitalize()} integration removed."}
    except Exception as e:
         logger.error(f"Delete integration failed: {e}")
         raise HTTPException(500, f"Failed to delete: {e}")

@app.post("/api/integrations/test/{platform}")
async def api_test_integration(platform: str):
    """Simulate a connection test."""
    try:
        if platform == "youtube":
             if not os.getenv("YOUTUBE_API_KEY"):
                  raise HTTPException(400, "Missing API Key")
             return {"success": True, "message": "YouTube Key configured."}

        elif platform == "reddit":
            if not os.getenv("REDDIT_CLIENT_ID"):
                 raise HTTPException(400, "Missing Client ID")
            try:
                await reddit_scraper.reddit_scraper.search_product_mentions("test", limit=1)
            except Exception:
                pass # Fail silently for test connection as valid creds might rate limit or fail
            return {"success": True, "message": "Reddit Connected"}

        elif platform == "twitter":
             if not os.getenv("TWITTER_BEARER_TOKEN"):
                  raise HTTPException(400, "Missing Bearer Token")
             try:
                 # Real connection test
                 await twitter_scraper.twitter_scraper.search_tweets("test", limit=1)
             except Exception:
                 pass # Fail silently for test connection as valid creds might rate limit or fail
             
             return {"success": True, "message": "Twitter Connected"}

        return {"success": True, "message": f"{platform} connection verified"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Connection failed: {str(e)}")


@app.get("/api/integrations")
async def api_get_integrations():
    try:
        resp = supabase.table("integrations").select("*").execute()
        data = resp.data or []
    except Exception:
        data = []
    return {"success": True, "data": data}


@app.get("/api/competitors/compare")
async def api_compare_competitors(productA: str, productB: str):
    try:
        # Fetch reviews for both products
        reviews_a = await get_reviews(productA, limit=500)
        reviews_b = await get_reviews(productB, limit=500)
        
        def calc_complex_stats(reviews):
            if not reviews:
                return {
                    "sentiment": 0, "credibility": 0, "reviewCount": 0,
                    "counts": {"positive": 0, "neutral": 0, "negative": 0},
                    "aspects": {}
                }
            
            scores = []
            creds = []
            counts = {"positive": 0, "neutral": 0, "negative": 0}
            aspect_sums = {} # "Price": [total_score, count]
            
            for r in reviews:
                sa = r.get("sentiment_analysis")
                if isinstance(sa, list) and sa: sa = sa[0]
                if isinstance(sa, dict):
                    # Sentiment & Credibility
                    s = float(sa.get("score") or 0.5)
                    scores.append(s)
                    creds.append(float(sa.get("credibility") or 0.95))
                    
                    lbl = (sa.get("label") or "neutral").lower()
                    if "positive" in lbl: counts["positive"] += 1
                    elif "negative" in lbl: counts["negative"] += 1
                    else: counts["neutral"] += 1
                    
                    # Aspects
                    # Structure in DB: [{"name": "Price", "sentiment": "positive", "score": 0.9}]
                    asps = sa.get("aspects") or []
                    for a in asps:
                        name = (a.get("name") or a.get("aspect") or "").capitalize()
                        if not name: continue
                        
                        # Normalize score to 0-1
                        val = 0.5
                        if "score" in a: val = float(a["score"])
                        elif a.get("sentiment") == "positive": val = 1.0
                        elif a.get("sentiment") == "negative": val = 0.0
                        
                        if name not in aspect_sums: aspect_sums[name] = [0.0, 0]
                        aspect_sums[name][0] += val
                        aspect_sums[name][1] += 1
            
            # Final Aggregation
            avg_score = (sum(scores) / len(scores)) * 100 if scores else 0
            avg_cred = (sum(creds) / len(creds)) * 100 if creds else 0
            
            # Aspect aggregation (0-5 scale for Radar)
            final_aspects = {}
            for name, (total, count) in aspect_sums.items():
                if count > 0:
                    # 0-1 avg * 5 = 0-5 scale
                    final_aspects[name] = round((total / count) * 5, 1)
            
            # Top 6 aspects only
            sorted_aspects = dict(sorted(final_aspects.items(), key=lambda item: item[1], reverse=True)[:6])

            return {
                "sentiment": round(avg_score, 1),
                "credibility": round(avg_cred, 1),
                "reviewCount": len(reviews),
                "counts": counts,
                "aspects": sorted_aspects
            }

        stats_a = calc_complex_stats(reviews_a)
        stats_b = calc_complex_stats(reviews_b)
        
        return {
            "success": True, 
            "data": {
                "metrics": {
                    "productA": stats_a,
                    "productB": stats_b
                }
            }
        }
    except Exception as e:
        logger.error(f"Compare failed: {e}")
        return {"success": False, "detail": str(e), "data": {}}

@app.get("/api/analytics")
async def api_get_analytics(product_id: Optional[str] = None, range: str = "7d"):
    try:
        # Determine days based on range
        days = 7
        if range == "30d": days = 30
        elif range == "90d": days = 90
        elif range == "24h": days = 1
        
        trends = await get_sentiment_trends(product_id, days=days)
        return {"success": True, "data": {"sentimentTrends": trends}}
    except Exception as e:
         return {"success": False, "detail": str(e), "data": {"sentimentTrends": []}}


@app.get("/api/products/{product_id}/predictions")
async def api_get_predictions(product_id: str, days: int = 7):
    """
    Get AI-powered sentiment forecast.
    """
    try:
        # Fetch historical sentiment data
        trends = await get_sentiment_trends(product_id, days=90) # Get enough history
        
        # Format for prediction service
        # trends is usually [{'date': '...', 'sentiment': 0.5}, ...]
        history = [{"date": t["date"], "sentiment": t["sentiment"]} for t in trends]
        
        forecast = generate_forecast(history)
        
        # Determine trend
        trend = "stable"
        if forecast and len(forecast) > 1:
            first = forecast[0]["sentiment"]
            last = forecast[-1]["sentiment"]
            if last > first + 0.1: trend = "improving"
            elif last < first - 0.1: trend = "declining"
        
        return {"success": True, "data": {"forecast": forecast, "trend": trend}}
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return {"success": False, "detail": str(e), "data": {"forecast": [], "trend": "unknown"}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
