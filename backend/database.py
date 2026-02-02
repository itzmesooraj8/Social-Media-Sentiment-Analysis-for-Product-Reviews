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



# Safe DB Wrapper
async def _safe_db_call(coroutine, timeout: float = 10.0) -> Any:
    # ...
    try:
        return await asyncio.wait_for(coroutine, timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(f"DB Call Timeout ({timeout}s) - switching to fallback/empty")
        return None
    except Exception as e:
        logger.error(f"DB Call Error: {e}")
        return None

# --- CACHE STORAGE ---
# Simple in-memory cache for dashboard stats
# Structure: {"data": dict, "expiry": timestamp}
_DASHBOARD_CACHE = {
    "data": {},
    "expiry": 0.0
}
_CACHE_TTL = 60 # seconds


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
    
    return []

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

    return None

async def get_reviews(product_id: str = None, limit: int = 100):
    if supabase is not None:
        try:
            query = supabase.table("reviews").select("*, sentiment_analysis(*)")
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

    return {"success": False, "error": "Supabase not connected"}

async def get_dashboard_stats():
    """
    Fetch aggregated stats for the dashboard with Caching and Parallelism.
    """
    if not supabase:
        return {}
        
    # 1. Check Cache
    import time
    now_ts = time.time()
    if _DASHBOARD_CACHE["data"] and now_ts < _DASHBOARD_CACHE["expiry"]:
        return _DASHBOARD_CACHE["data"]

    try:
        # Define tasks for parallel execution
        
        # Task 1: Total Reviews
        async def fetch_count():
            task = asyncio.to_thread(lambda: supabase.table("reviews").select("id", count="exact").execute())
            resp = await _safe_db_call(task)
            return resp.count if resp else 0
            
        # Task 2: Sentiment Stats (for avg score, credibility, bots, emotions)
        async def fetch_stats():
            task = asyncio.to_thread(lambda: supabase.table("sentiment_analysis").select("score, label, credibility, emotions").limit(200).execute())
            resp = await _safe_db_call(task)
            return resp.data if resp else []

        # Task 3: Delta Calculation (Today vs Yesterday)
        async def fetch_delta():
            try:
                now = datetime.now(timezone.utc)
                one_day_ago = now - timedelta(days=1)
                two_days_ago = now - timedelta(days=2)
                
                # Nested parallel tasks for dates - Limit to 200 to prevent timeout
                t_today = asyncio.to_thread(lambda: supabase.table("reviews").select("sentiment_analysis(score)")\
                    .gte("created_at", one_day_ago.isoformat()).limit(200).execute())
                t_yesterday = asyncio.to_thread(lambda: supabase.table("reviews").select("sentiment_analysis(score)")\
                    .gte("created_at", two_days_ago.isoformat()).lt("created_at", one_day_ago.isoformat()).limit(200).execute())
                    
                resp_today, resp_yesterday = await asyncio.gather(_safe_db_call(t_today), _safe_db_call(t_yesterday))
                
                # Helper for fallback structure parsing if API changes
                def safe_extract_scores(resp):
                    if not resp or not resp.data: return []
                    s_list = []
                    for r in resp.data:
                        sa = r.get("sentiment_analysis")
                        if isinstance(sa, list) and sa: sa = sa[0]
                        if isinstance(sa, dict) and sa.get("score") is not None:
                             s_list.append(float(sa.get("score")))
                    return s_list

                scores_today = safe_extract_scores(resp_today)
                scores_yesterday = safe_extract_scores(resp_yesterday)
                
                val_today = (sum(scores_today)/len(scores_today))*100 if scores_today else 0.0
                val_yesterday = (sum(scores_yesterday)/len(scores_yesterday))*100 if scores_yesterday else 0.0
                
                return val_today - val_yesterday if val_yesterday > 0 else 0.0
            except Exception as e:
                logger.error(f"Delta error: {e}")
                return 0.0

        # Task 4: Platform Breakdown
        async def fetch_platforms():
            task = asyncio.to_thread(lambda: supabase.table("reviews").select("platform, sentiment_analysis(label)").limit(200).execute())
            resp = await _safe_db_call(task)
            rows = resp.data if resp else []
            
            platforms = {}
            for r in rows:
                p = (r.get("platform") or "unknown").lower()
                if p not in platforms: platforms[p] = {"positive":0,"neutral":0,"negative":0,"total":0}
                platforms[p]["total"] += 1
                
                sa = r.get("sentiment_analysis")
                if isinstance(sa, list) and sa: sa = sa[0]
                label = (sa.get("label") or "neutral").lower() if sa else "neutral"
                
                if "positive" in label: platforms[p]["positive"] += 1
                elif "negative" in label: platforms[p]["negative"] += 1
                else: platforms[p]["neutral"] += 1
            
            return [{
                "platform": k, "positive": v["positive"], "neutral": v["neutral"], 
                "negative": v["negative"], "count": v["total"]
            } for k, v in platforms.items()]

        # Task 5: Recent Reviews
        async def fetch_recent():
            task = asyncio.to_thread(lambda: supabase.table("reviews").select("*, sentiment_analysis(*)").order("created_at", desc=True).limit(10).execute())
            resp = await _safe_db_call(task)
            return resp.data if resp else []

        # Task 6: Top Keywords/Topics (God Tier)
        async def fetch_keywords():
             try:
                 # Fetch topics
                 resp = await asyncio.to_thread(lambda: supabase.table("topic_analysis").select("*").order("size", desc=True).limit(20).execute())
                 if resp and resp.data:
                     # Unique by name
                     seen = set()
                     unique = []
                     for d in resp.data:
                         if d["topic_name"] not in seen:
                             unique.append({"text": d["topic_name"], "value": d.get("size", 10)})
                             seen.add(d["topic_name"])
                     return unique
                 return []
             except Exception:
                 return []

        # EXECUTE ALL IN PARALLEL
        results = await asyncio.gather(
            fetch_count(),
            fetch_stats(),
            fetch_delta(),
            fetch_platforms(),
            fetch_recent(),
            fetch_keywords()
        )
        
        total_reviews, stats_rows, sentiment_delta, platform_breakdown, recent_reviews, top_keywords = results

        # Process stats
        avg_score = 0
        avg_credibility = 0
        bots_detected = 0
        emotion_counts = {}
        
        if stats_rows:
            scores = []
            creds = []
            for r in stats_rows:
                s = r.get("score")
                c = r.get("credibility")
                if s is not None: scores.append(float(s))
                if c is not None: creds.append(float(c))
                
                # God Tier Emotion Aggregation
                # Check for detailed 'emotions' list first
                emos = r.get("emotions")
                if emos and isinstance(emos, list) and len(emos) > 0:
                    # emos is [{"name": "joy", "score": 90}]
                    primary = emos[0].get("name")
                    if primary:
                        emotion_counts[primary] = emotion_counts.get(primary, 0) + 1
                else:
                    # Fallback to label
                    label = r.get("label")
                    if label:
                         emo = "Neutral"
                         if label == "POSITIVE": emo = "Joy"
                         elif label == "NEGATIVE": emo = "Sadness"
                         emotion_counts[emo] = emotion_counts.get(emo, 0) + 1
            
            if scores: avg_score = (sum(scores) / len(scores)) * 100
            if creds: avg_credibility = (sum(creds) / len(creds)) * 100
            bots_detected = sum(1 for c in creds if c < 0.4)

        # Better Emotion Breakdown (Normalized)
        total_emotions = sum(emotion_counts.values()) or 1
        emotion_breakdown = [{"name": k, "value": v, "percentage": round((v/total_emotions)*100, 1)} for k,v in emotion_counts.items()]

        final_data = {
            "recentReviews": recent_reviews,
            "totalReviews": total_reviews,
            "sentimentScore": round(avg_score, 1),
            "sentimentDelta": round(sentiment_delta, 1),
            "averageCredibility": round(avg_credibility, 1),
            "platformBreakdown": platform_breakdown,
            "credibilityReport": {
                "overallScore": round(avg_credibility, 1),
                "verifiedReviews": total_reviews - bots_detected,
                "botsDetected": bots_detected
            },
            "sentimentTrends": [], 
            "topKeywords": top_keywords,
            "emotionBreakdown": emotion_breakdown,
            "alerts": [] 
        }
        
        # Save to Cache
        _DASHBOARD_CACHE["data"] = final_data
        _DASHBOARD_CACHE["expiry"] = time.time() + _CACHE_TTL
        
        return final_data

    except Exception as e:
        logger.error(f"get_dashboard_stats failed: {e}")
        # Return default structure to prevent Frontend Crash
        return {
            "recentReviews": [],
            "totalReviews": 0,
            "sentimentScore": 0,
            "sentimentDelta": 0,
            "averageCredibility": 0,
            "platformBreakdown": [],
            "credibilityReport": {
                "overallScore": 0,
                "verifiedReviews": 0,
                "botsDetected": 0
            },
            "sentimentTrends": [], 
            "topKeywords": [],
            "emotionBreakdown": [],
            "alerts": [] 
        }

async def save_sentiment_analysis(analysis_data: dict):
    if supabase:
        task = asyncio.to_thread(lambda: supabase.table("sentiment_analysis").insert(analysis_data).execute())
        await _safe_db_call(task)

async def save_review(review_data: dict):
    """Async wrapper for saving review."""
    if supabase is not None:
        try:
            task = asyncio.to_thread(lambda: supabase.table("reviews").insert(review_data).execute())
            resp = await _safe_db_call(task)
            if resp and resp.data:
                return resp.data[0]
        except Exception as e:
            # Handle duplicate or constraint errors generally
            # Caller might want to know specific error, but for now log and return None
            # If we want to allow caller to retry (duplicate), we should re-raise or return specific error.
            # But the caller in data_pipeline checks for 'duplicate' in string.
            # We can re-raise exception if it occurs in _safe_db_call? 
            # _safe_db_call returns None on error.
            # We should probably modify _safe_db_call or just implement simple logic here.
            logger.error(f"save_review failed: {e}")
            raise e # Let caller handle logic
    return None

async def save_topic(topic_data: dict):
    if supabase:
        task = asyncio.to_thread(lambda: supabase.table("topic_analysis").insert(topic_data).execute())
        await _safe_db_call(task)

async def create_alert_log(alert_data: dict):
    if supabase:
        task = asyncio.to_thread(lambda: supabase.table("alerts").insert(alert_data).execute())
        await _safe_db_call(task)