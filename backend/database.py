import os
import asyncio
import json
import logging
import re
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
_CACHE_TTL = 10 # seconds


async def get_sentiment_trends(product_id: str = None, days: int = 30) -> List[Dict[str, Any]]:
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
                .gte("created_at", start_date.isoformat())\
                .order("created_at", desc=False)
            
            if product_id:
                query = query.eq("product_id", product_id)
                
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
            # 1. Delete Sentiment Analysis (Linked by product_id)
            # We do this first to prevent orphans if they are not constrained
            t1 = asyncio.to_thread(lambda: supabase.table("sentiment_analysis").delete().eq("product_id", product_id).execute())
            await _safe_db_call(t1)

            # 2. Delete Reviews (Linked by product_id)
            t2 = asyncio.to_thread(lambda: supabase.table("reviews").delete().eq("product_id", product_id).execute())
            await _safe_db_call(t2)
            
            # 3. Delete Product
            t3 = asyncio.to_thread(lambda: supabase.table("products").delete().eq("id", product_id).execute())
            resp = await _safe_db_call(t3)
            
            # 4. Cleanup orphans just in case
            await cleanup_orphaned_data()
            
            if resp: # Success
                return {"success": True, "deleted_id": product_id}
        except Exception as e:
            logger.error(f"Delete product failed: {e}")
            pass

    return {"success": False, "error": "Supabase not connected"}

async def cleanup_orphaned_data():
    """
    Remove data that is not linked to any valid product or review.
    """
    if not supabase: return
    
    try:
        # Get all valid product IDs
        p_task = asyncio.to_thread(lambda: supabase.table("products").select("id").execute())
        p_resp = await _safe_db_call(p_task)
        valid_p_ids = [p['id'] for p in p_resp.data] if p_resp and p_resp.data else []
        
        # 1. Delete Reviews with invalid product_id
        if valid_p_ids:
             # Deleting using 'not.in' filter
             # Note: PostgREST syntax for 'not in' is .not_.in_, but supabase-py might vary. 
             # Safe fallback: Let's assume we can't easily do 'NOT IN' huge list.
             # Instead: Delete where product_id is NULL
             t_null = asyncio.to_thread(lambda: supabase.table("reviews").delete().is_("product_id", "null").execute())
             await _safe_db_call(t_null)
        else:
             # If NO products exist, ALL reviews should be deleted?
             # Yes, if valid_p_ids is empty, we must wipe reviews to be safe (if logic assumes reviews must have product)
             count_task = asyncio.to_thread(lambda: supabase.table("reviews").select("id", count="exact").execute())
             c_resp = await _safe_db_call(count_task)
             if c_resp and c_resp.count > 0:
                 logger.warning("No products found, wiping orphaned reviews...")
                 # Delete all
                 # supabase-py doesn't like delete without filter usually, need a catch-all if allowed or multiple batches
                 # neq '0' usually works if scanning is allowed
                 t_wipe = asyncio.to_thread(lambda: supabase.table("reviews").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()) 
                 await _safe_db_call(t_wipe)

        # 2. Delete Sentiment Analysis with linked review_id/product_id issue
        # Harder to check efficiently without stored proc.
        # But if we deleted reviews, chances are SA data is orphaned if no cascade.
        # If no products, wipe SA
        if not valid_p_ids:
             # If ID is BigInt, this works. If UUID, it fails. 
             # Based on previous error, likely UUID or we can use a different trick.
             # Safest filter for "All" is usually checking a column that is always not null, e.g. 'created_at' > '1970...'
             # But let's try UUID neutral approach or string zero for UUID
             t_wipe_sa = asyncio.to_thread(lambda: supabase.table("sentiment_analysis").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()) 
             await _safe_db_call(t_wipe_sa)
             
             # Also wipe topic analysis? Topics are global but maybe we should reset
             # t_wipe_ta = asyncio.to_thread(lambda: supabase.table("topic_analysis").delete().neq("id", 0).execute())
             # await _safe_db_call(t_wipe_ta)

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")

async def get_dashboard_stats(product_id: str = None):
    """
    Fetch aggregated stats for the dashboard with Caching and Parallelism.
    Now supports filtering by product_id.
    """
    if not supabase:
        return {}
        
    # 1. Check Cache
    import time
    now_ts = time.time()
    cache_key = f"data_{product_id}" if product_id else "data"
    
    if _DASHBOARD_CACHE.get(cache_key) and now_ts < _DASHBOARD_CACHE.get("expiry", 0):
        return _DASHBOARD_CACHE[cache_key]

    try:
        # Define tasks for parallel execution
        
        # Task 1: Total Reviews
        async def fetch_count():
            query = supabase.table("reviews").select("id", count="exact")
            if product_id: query = query.eq("product_id", product_id)
            task = asyncio.to_thread(lambda: query.execute())
            resp = await _safe_db_call(task)
            return resp.count if resp else 0
            
        # Task 2: Sentiment Stats (for avg score, credibility, bots, emotions)
        # Re-defining fetch_stats to include aspects
        async def fetch_stats_enhanced():
            query = supabase.table("sentiment_analysis").select("score, label, credibility, emotions, aspects").limit(200)
            if product_id: query = query.eq("product_id", product_id)
            task = asyncio.to_thread(lambda: query.execute())
            resp = await _safe_db_call(task)
            return resp.data if resp else []

        # Task 3: Delta Calculation (Today vs Yesterday)
        async def fetch_delta():
            try:
                now = datetime.now(timezone.utc)
                one_day_ago = now - timedelta(days=1)
                two_days_ago = now - timedelta(days=2)
                
                # Nested parallel tasks for dates - Limit to 200
                q1 = supabase.table("reviews").select("sentiment_analysis(score)")\
                    .gte("created_at", one_day_ago.isoformat()).limit(200)
                if product_id: q1 = q1.eq("product_id", product_id)
                
                q2 = supabase.table("reviews").select("sentiment_analysis(score)")\
                    .gte("created_at", two_days_ago.isoformat()).lt("created_at", one_day_ago.isoformat()).limit(200)
                if product_id: q2 = q2.eq("product_id", product_id)

                t_today = asyncio.to_thread(lambda: q1.execute())
                t_yesterday = asyncio.to_thread(lambda: q2.execute())
                    
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
            query = supabase.table("reviews").select("platform, sentiment_analysis(label)").limit(200)
            if product_id: query = query.eq("product_id", product_id)
            task = asyncio.to_thread(lambda: query.execute())
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
            query = supabase.table("reviews").select("*, sentiment_analysis(*)").order("created_at", desc=True).limit(10)
            if product_id: query = query.eq("product_id", product_id)
            task = asyncio.to_thread(lambda: query.execute())
            resp = await _safe_db_call(task)
            return resp.data if resp else []

        # Task 6: Top Keywords/Topics (God Tier)
        async def fetch_keywords():
             try:
                 # If product_id, we can't use global 'topic_analysis' easily as it lacks product_id.
                 # So we extract from recent reviews text.
                 if product_id:
                     # Let's fetch text column from reviews for this product
                     q = supabase.table("reviews").select("content").eq("product_id", product_id).limit(100)
                     t = asyncio.to_thread(lambda: q.execute())
                     resp = await _safe_db_call(t)
                     if resp and resp.data:
                         text_blob = " ".join([r.get("content", "") for r in resp.data if r.get("content")])
                         from collections import Counter
                         import re
                         words = re.findall(r'\w+', text_blob.lower())
                         stop = {"the", "and", "is", "it", "to", "in", "of", "for", "with", "on", "this", "that", "are", "was", "product", "review", "i", "my", "a", "an", "just", "get", "can", "very", "really"}
                         filtered = [w for w in words if len(w)>3 and w not in stop]
                         common = Counter(filtered).most_common(10)
                         return [{"text": w, "value": c} for w, c in common]
                     return []
                 
                 # Global: Fetch topics from topic_analysis
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
                 
        # EXECUTE SEQUENTIALLY TO DEBUG HANGING
        logger.info(f"Starting dashboard stats fetch (sequential) for p={product_id}...")
        
        # 1. Count
        total_reviews = await fetch_count()
        logger.info(f"Got count: {total_reviews}")
        
        # 2. Stats (Enhanced)
        stats_rows = await fetch_stats_enhanced()
        logger.info(f"Got stats: {len(stats_rows)} rows")
        
        # 3. Delta
        sentiment_delta = await fetch_delta()
        logger.info(f"Got delta: {sentiment_delta}")
        
        # 4. Platforms
        platform_breakdown = await fetch_platforms()
        logger.info("Got platforms")
        
        # 5. Recent
        recent_reviews = await fetch_recent()
        logger.info("Got recent")
        
        # 6. Keywords
        top_keywords = await fetch_keywords()
        logger.info("Got keywords")
        
        # results = await asyncio.gather(
        #     fetch_count(),
        #     fetch_stats(),
        #     fetch_delta(),
        #     fetch_platforms(),
        #     fetch_recent(),
        #     fetch_keywords()
        # )
        
        # total_reviews, stats_rows, sentiment_delta, platform_breakdown, recent_reviews, top_keywords = results

        # Process stats
        avg_score = 0
        avg_credibility = 0
        bots_detected = 0
        emotion_counts = {}
        aspect_scores = {}
        
        if stats_rows:
            scores = []
            creds = []
            for r in stats_rows:
                s = r.get("score")
                c = r.get("credibility")
                if s is not None: scores.append(float(s))
                if c is not None: creds.append(float(c))
                
                # Emotions
                emos = r.get("emotions")
                if emos and isinstance(emos, list) and len(emos) > 0:
                    primary = emos[0].get("name")
                    if primary:
                        emotion_counts[primary] = emotion_counts.get(primary, 0) + 1
                else:
                    label = r.get("label")
                    if label:
                         emo = "Neutral"
                         if label == "POSITIVE": emo = "Joy"
                         elif label == "NEGATIVE": emo = "Sadness"
                         emotion_counts[emo] = emotion_counts.get(emo, 0) + 1
                
                # Aspects
                asps = r.get("aspects")
                if asps and isinstance(asps, list):
                     for a in asps:
                         name = a.get("name") or a.get("aspect")
                         if name:
                             name = name.capitalize()
                             val = 1
                             if a.get("sentiment") == "positive": val = 5
                             elif a.get("sentiment") == "negative": val = 1
                             elif "score" in a: val = float(a["score"]) * 5
                             else: val = 3
                             
                             if name not in aspect_scores: aspect_scores[name] = {"sum": 0, "n": 0}
                             aspect_scores[name]["sum"] += val
                             aspect_scores[name]["n"] += 1

            if scores: avg_score = (sum(scores) / len(scores)) * 100
            if creds: avg_credibility = (sum(creds) / len(creds)) * 100
            bots_detected = sum(1 for c in creds if c < 0.4)

        # Emotion Breakdown
        total_emotions = sum(emotion_counts.values()) or 1
        emotion_breakdown = [{"name": k, "value": v, "percentage": round((v/total_emotions)*100, 1)} for k,v in emotion_counts.items()]
        
        # Aspect Scores
        final_aspects = []
        for k, v in aspect_scores.items():
            if v["n"] > 0:
                final_aspects.append({"aspect": k, "score": round(v["sum"]/v["n"], 1), "fullMark": 5})
        final_aspects.sort(key=lambda x: x["score"], reverse=True)
        final_aspects = final_aspects[:6]

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
            "aspectScores": final_aspects,
            "alerts": [] 
        }
        
        # Save to Cache ONLY if we found data, to avoid caching failures/empty states
        if total_reviews > 0:
            _DASHBOARD_CACHE[cache_key] = final_data
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
            "aspectScores": [],
            "alerts": [] 
        }

async def get_product_stats_full(product_id: str):
    """
    Fetch comprehensive stats for a single product, including emotions and aspects.
    """
    if not supabase: return None
    
    try:
        # 1. Fetch Reviews with Sentiment Data
        # increasing limit to ensure we get enough data for meaningful stats
        rows_task = asyncio.to_thread(lambda: supabase.table("reviews").select("*, sentiment_analysis(*)").eq("product_id", product_id).limit(500).execute())
        resp = await _safe_db_call(rows_task)
        rows = resp.data if resp else []
        
        if not rows:
            return {
                "total_reviews": 0,
                "average_sentiment": 0,
                "positive_percent": 0,
                "credibility_score": 0,
                "emotions": [],
                "aspects": [],
                "keywords": []
            }

        scores = []
        creds = []
        positive_count = 0
        emotion_counts = {}
        aspect_scores = {} # "Price": {"sum": 0, "count": 0}
        
        for r in rows:
            sa = r.get("sentiment_analysis")
            if isinstance(sa, list) and sa: sa = sa[0]
            if sa and isinstance(sa, dict):
                # Basic Stats
                s = float(sa.get("score") or 0.5)
                c = float(sa.get("credibility") or 0.95)
                scores.append(s)
                creds.append(c)
                if sa.get("label") == "POSITIVE": positive_count += 1
                
                # Emotions
                emos = sa.get("emotions") or []
                if emos and isinstance(emos, list) and len(emos) > 0:
                    primary = emos[0].get("name")
                    if primary:
                        emotion_counts[primary] = emotion_counts.get(primary, 0) + 1
                else:
                    # Fallback emotion from label
                    lbl = sa.get("label")
                    if lbl == "POSITIVE": e = "Joy"
                    elif lbl == "NEGATIVE": e = "Disappointment"
                    else: e = "Neutral"
                    emotion_counts[e] = emotion_counts.get(e, 0) + 1

                # Aspects
                asps = sa.get("aspects") or []
                # asps structure: [{"name": "Price", "sentiment": "positive"}] (simple) 
                # OR [{"aspect": "Price", "score": 0.8}] (complex)
                # Let's handle both or what data_pipeline saves.
                # data_pipeline saves: "aspects": analysis.get("aspects", [])
                # ai_service usually returns: [{"name": "Quality", "sentiment": "positive"}]
                for a in asps:
                    name = a.get("name") or a.get("aspect")
                    if not name: continue
                    name = name.capitalize()
                    
                    if name not in aspect_scores: aspect_scores[name] = {"val": 0, "n": 0}
                    
                    # Heuristic score from sentiment label if numerical score missing
                    val = 0.5
                    if "score" in a: val = float(a["score"])
                    elif a.get("sentiment") == "positive": val = 1.0
                    elif a.get("sentiment") == "negative": val = 0.0
                    
                    aspect_scores[name]["val"] += val
                    aspect_scores[name]["n"] += 1

        avg_score = (sum(scores) / len(scores)) * 100 if scores else 0
        avg_cred = (sum(creds) / len(creds)) * 100 if creds else 0
        pos_percent = (positive_count / len(rows)) * 100 if rows else 0
        
        # Format Emotions for Chart [{name, value}]
        formatted_emotions = [{"name": k, "value": v} for k,v in emotion_counts.items()]
        # Sort by value
        formatted_emotions.sort(key=lambda x: x["value"], reverse=True)
        
        # Format Aspects for Chart [{name, score}] (score 0-100)
        formatted_aspects = []
        for k, v in aspect_scores.items():
            if v["n"] > 0:
                final_s = (v["val"] / v["n"]) * 100
                formatted_aspects.append({"name": k, "score": int(final_s)})
        formatted_aspects.sort(key=lambda x: x["score"], reverse=True)

        # 2. Keywords (from topic_analysis or extract)
        # Try topic_analysis first (filtered? No, topic_analysis schema in dump doesn't have product_id usually... wait)
        # Checked schema_dump.sql earlier: 
        # create table if not exists topic_analysis ( id ..., topic_name text, sentiment numeric, size integer, keywords text[], created_at ... )
        # NO product_id in topic_analysis table in schema_dump.sql!
        # This means topics are global or "orphaned".
        # We must extract from review content for *this* product specifically if we want accuracy.
        # But for speed, let's just do a simple word freq on the fetched reviews content since we have them in memory (up to 500).
        
        keywords = []
        try:
            from collections import Counter
            all_text = " ".join([r.get("content", "") for r in rows if r.get("content")])
            # Very basic cleanup
            words = re.findall(r'\w+', all_text.lower())
            stop_words = {"the", "and", "a", "to", "of", "in", "it", "is", "for", "that", "on", "with", "this", "but", "not", "are", "was", "have", "as", "be", "an", "or", "at", "if", "so", "my", "you", "i", "very", "really", "product", "just", "get", "can"}
            filtered = [w for w in words if w not in stop_words and len(w) > 3]
            common = Counter(filtered).most_common(10)
            keywords = [{"text": w, "value": c} for w, c in common]
        except Exception:
            pass

        return {
            "total_reviews": len(rows),
            "totalReviews": len(rows), # Alias for frontend safety
            "average_sentiment": round(avg_score, 1),
            "avgSentiment": round(avg_score, 1),
            "positive_percent": round(pos_percent, 1),
            "credibility_score": round(avg_cred, 1),
            "credibilityScore": round(avg_cred, 1),
            "emotions": formatted_emotions[:6],
            "aspects": formatted_aspects[:6],
            "keywords": keywords
        }
    except Exception as e:
        logger.error(f"get_product_stats_full failed: {e}")
        return None

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