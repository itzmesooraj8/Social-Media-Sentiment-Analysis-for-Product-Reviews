import os
import asyncio
import json
import logging
from pathlib import Path
from typing import Any, List, Dict, Optional
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client
from dotenv import load_dotenv

# Setup Logger
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Initialize Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY or "your_supabase_url_here" in SUPABASE_URL:
    logger.critical("Supabase credentials not found or invalid. Using local fallback.")
    supabase: Client = None
else:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing Supabase client: {e}")
        supabase = None

def _write_local_db(data: dict):
    try:
        _LOCAL_DB_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as e:
        logger.error(f"Failed to write local DB: {e}")

# Safe DB Wrapper
async def _safe_db_call(coroutine, timeout: float = 30.0) -> Any:
    # ...
    try:
        return await asyncio.wait_for(coroutine, timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(f"DB Call Timeout ({timeout}s) - switching to fallback/empty")
        return None
    except Exception as e:
        logger.error(f"DB Call Error: {e}")
        return None


async def get_sentiment_trends(product_id: str, days: int = 30) -> List[Dict[str, Any]]:
    """
    Fetch sentiment trend data for a specific period.
    Returns list of {created_at, score, label}
    """
    if supabase is not None:
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Efficient join query
            query = supabase.table("reviews")\
                .select("created_at, sentiment_analysis(score, label)")\
                .eq("product_id", product_id)\
                .gte("created_at", start_date.isoformat())\
                .order("created_at", desc=False)
                
            task = asyncio.to_thread(lambda: query.execute())
            resp = await _safe_db_call(task)
            
            if resp and resp.data:
                # Flatten structure
                flattened = []
                for r in resp.data:
                    sa = r.get("sentiment_analysis")
                    if isinstance(sa, list) and sa: sa = sa[0]
                    if sa:
                        flattened.append({
                            "created_at": r.get("created_at"),
                            "score": sa.get("score"),
                            "label": sa.get("label")
                        })
                return flattened
        except Exception as e:
            logger.error(f"get_sentiment_trends failed: {e}")
            
    return []

# Database helper functions
async def get_products():
    """Fetch all products from the database."""
    if supabase is not None:
        try:
            # We use a lambda to defer execution until to_thread
            # But asyncio.to_thread runs sync code. 
            # We wrap the to_thread task in wait_for.
            task = asyncio.to_thread(lambda: supabase.table("products").select("*").limit(50).execute())
            response = await _safe_db_call(task)
            
            if response and hasattr(response, 'data'):
                return response.data
        except Exception as e:
            logger.error(f"Supabase get_products failed: {e}")
    
    # Fallback to local JSON
    db = _read_local_db()
    return db.get("products", [])

async def add_product(product_data: dict):
    """Add a new product to the database."""
    if supabase is not None:
        try:
            task = asyncio.to_thread(lambda: supabase.table("products").insert(product_data).execute())
            response = await _safe_db_call(task)
            
            if response and hasattr(response, 'data'):
                return response.data
        except Exception as e:
            logger.error(f"Supabase add_product failed: {e}")

    # Fallback
    import uuid
    db = _read_local_db()
    prod = {**product_data}
    if not prod.get("id"):
        prod["id"] = str(uuid.uuid4())
    db.setdefault("products", []).append(prod)
    _write_local_db(db)
    return prod

async def get_reviews(product_id: str = None, limit: int = 100):
    if supabase is not None:
        try:
            query = supabase.table("reviews").select("*")
            if product_id:
                query = query.eq("product_id", product_id)
            
            task = asyncio.to_thread(lambda: query.limit(limit).order("created_at", desc=True).execute())
            response = await _safe_db_call(task)
            
            if response and hasattr(response, 'data'):
                return response.data
        except Exception as e:
            logger.error(f"Supabase get_reviews failed: {e}")
            
    return [] # Fallback empty

async def get_product_by_id(product_id: str):
    if supabase is not None:
        try:
            task = asyncio.to_thread(lambda: supabase.table("products").select("*").eq("id", product_id).limit(1).execute())
            resp = await _safe_db_call(task)
            if resp and resp.data:
                return resp.data[0]
        except Exception:
            pass

    db = _read_local_db()
    for p in db.get("products", []):
        if str(p.get("id")) == str(product_id):
            return p
    return None

async def delete_product(product_id: str):
    if supabase is not None:
        try:
            # Reviews delete
            task1 = asyncio.to_thread(lambda: supabase.table("reviews").delete().eq("product_id", product_id).execute())
            await _safe_db_call(task1) # Best effort
            
            # Product delete
            task2 = asyncio.to_thread(lambda: supabase.table("products").delete().eq("id", product_id).execute())
            resp = await _safe_db_call(task2)
            
            if resp: # Success
                return {"success": True, "deleted_id": product_id}
        except Exception:
            pass

    # Fallback
    db = _read_local_db()
    prods = db.get("products", [])
    new_prods = [p for p in prods if str(p.get("id")) != str(product_id)]
    db["products"] = new_prods
    reviews = db.get("reviews", [])
    db["reviews"] = [r for r in reviews if str(r.get("product_id")) != str(product_id)]
    _write_local_db(db)
    return {"success": True, "deleted_id": product_id}

async def get_dashboard_stats():
    """
    Fetch aggregated stats for the dashboard.
    """
    if not supabase:
        return {}

    try:
        # 1. Total Reviews
        # Using exact count for speed if table is large, or just normal count
        task_count = asyncio.to_thread(lambda: supabase.table("reviews").select("id", count="exact").execute())
        resp_count = await _safe_db_call(task_count)
        total_reviews = resp_count.count if resp_count else 0
        
        # 2. Average Sentiment & Bot Count
        # Fetching stats from sentiment_analysis table
        task_stats = asyncio.to_thread(lambda: supabase.table("sentiment_analysis").select("score, label, credibility").limit(2000).execute())
        resp_stats = await _safe_db_call(task_stats)
        
        avg_score = 0
        bots_detected = 0
        avg_credibility = 0
        sentiment_delta = 0.0 # Placeholder for now, requires historical comparison
        
        rows = resp_stats.data if resp_stats else []
        if rows:
            scores = [r.get("score") for r in rows if r.get("score") is not None]
            creds = [r.get("credibility") for r in rows if r.get("credibility") is not None]
            
            if scores: avg_score = (sum(scores) / len(scores)) * 100 # 0-100 scale
            if creds: avg_credibility = (sum(creds) / len(creds)) * 100
            
            # Simple bot detection logic (credibility < 0.4)
            bots_detected = sum(1 for c in creds if c < 0.4)
            
        # 3. Platform Breakdown
        # We need to group by platform. Supabase JS/Py client doesn't do 'group by' easily without RPC.
        # We'll fetch 'platform' from reviews and aggregation in python for now (limit 2000).
        # 3. Platform Breakdown (with Sentiment)
        task_platform = asyncio.to_thread(lambda: supabase.table("reviews").select("platform, sentiment_analysis(label)").limit(2000).execute())
        resp_platform = await _safe_db_call(task_platform)
        platform_rows = resp_platform.data if resp_platform else []
        
        platforms = {}
        # platforms structure: { 'twitter': { 'positive': 10, 'neutral': 5, 'negative': 2, 'count': 17 } }

        for r in platform_rows:
            p = r.get("platform") or "unknown"
            p = p.lower()
            
            if p not in platforms:
                platforms[p] = {"positive": 0, "neutral": 0, "negative": 0, "total": 0}
            
            platforms[p]["total"] += 1
            
            # Extract sentiment label
            sa = r.get("sentiment_analysis")
            if isinstance(sa, list) and sa: sa = sa[0] # Handle list return
            label = (sa.get("label") or "neutral").lower() if sa else "neutral"
            
            if "positive" in label:
                platforms[p]["positive"] += 1
            elif "negative" in label:
                platforms[p]["negative"] += 1
            else:
                platforms[p]["neutral"] += 1
            
        platform_breakdown = [
            {
                "platform": k, 
                "positive": v["positive"], 
                "neutral": v["neutral"], 
                "negative": v["negative"],
                "count": v["total"]
            } 
            for k, v in platforms.items()
        ]

        return {
            "totalReviews": total_reviews,
            "sentimentScore": round(avg_score, 1),
            "sentimentDelta": sentiment_delta,
            "averageCredibility": round(avg_credibility, 1),
            "platformBreakdown": platform_breakdown,
            "credibilityReport": {
                "overallScore": round(avg_credibility, 1),
                "verifiedReviews": total_reviews - bots_detected, # approx
                "botsDetected": bots_detected
            },
            # Basic defaults for others to avoid crashes
            "sentimentTrends": [], 
            "topKeywords": [],
            "alerts": [] 
        }

    except Exception as e:
        logger.error(f"get_dashboard_stats failed: {e}")
        return {}

async def save_sentiment_analysis(analysis_data: dict):
    if supabase:
        task = asyncio.to_thread(lambda: supabase.table("sentiment_analysis").insert(analysis_data).execute())
        await _safe_db_call(task)