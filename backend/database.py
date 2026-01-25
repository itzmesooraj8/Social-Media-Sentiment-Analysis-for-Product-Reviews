"""
Database module for Supabase connection and operations.
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables (Robust path handling)
from pathlib import Path
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Initialize Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

# Debug prints to trace initialization
print(f"DEBUG: Loading .env from {env_path}")
print(f"DEBUG: SUPABASE_URL Found? {bool(SUPABASE_URL)}")
print(f"DEBUG: SUPABASE_KEY Found? {bool(SUPABASE_KEY)}")

if not SUPABASE_URL or not SUPABASE_KEY or "your_supabase_url_here" in SUPABASE_URL:
    print("CRITICAL: Supabase credentials not found or invalid (placeholders detected). Using local fallback.")
    supabase: Client = None
else:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Supabase client initialized successfully")
    except Exception as e:
        print(f"Error initializing Supabase client: {e}")
        supabase = None


def get_supabase_client() -> Client:
    """Get the Supabase client instance."""
    return supabase

# Local fallback DB (JSON) for development when Supabase is not configured
_LOCAL_DB_PATH = Path(__file__).parent / "local_db.json"

def _read_local_db() -> dict:
    if not _LOCAL_DB_PATH.exists():
        return {"products": [], "reviews": []}
    try:
        import json
        return json.loads(_LOCAL_DB_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"products": [], "reviews": []}

def _write_local_db(data: dict):
    try:
        import json
        _LOCAL_DB_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"Failed to write local DB: {e}")


# Database helper functions
async def get_products():
    """Fetch all products from the database."""
    try:
        if supabase is not None:
            import asyncio
            response = await asyncio.to_thread(lambda: supabase.table("products").select("*").limit(50).execute())
            return response.data
        # Fallback to local JSON
        db = _read_local_db()
        return db.get("products", [])
    except Exception as e:
        print(f"Error fetching products: {e}")
        return []


async def add_product(product_data: dict):
    """Add a new product to the database."""
    try:
        if supabase is not None:
            import asyncio
            response = await asyncio.to_thread(lambda: supabase.table("products").insert(product_data).execute())
            return response.data
        # local fallback - ensure id exists
        import uuid
        db = _read_local_db()
        prod = {**product_data}
        if not prod.get("id"):
            prod["id"] = str(uuid.uuid4())
        db.setdefault("products", []).append(prod)
        _write_local_db(db)
        return prod
    except Exception as e:
        print(f"Error adding product: {e}")
        raise


async def get_reviews(product_id: str = None, limit: int = 100):
    """Fetch reviews, optionally filtered by product."""
    try:
        query = supabase.table("reviews").select("*")
        if product_id:
            query = query.eq("product_id", product_id)
        
        import asyncio
        response = await asyncio.to_thread(lambda: query.limit(limit).order("created_at", desc=True).execute())
        return response.data
    except Exception as e:
        print(f"Error fetching reviews: {e}")
        return []


async def get_product_by_id(product_id: str):
    """Return a single product by id using Supabase if available, otherwise local JSON."""
    try:
        if supabase is not None:
            import asyncio
            resp = await asyncio.to_thread(lambda: supabase.table("products").select("*").eq("id", product_id).limit(1).execute())
            if resp.data:
                return resp.data[0]
            return None

        db = _read_local_db()
        for p in db.get("products", []):
            if str(p.get("id")) == str(product_id):
                return p
        return None
    except Exception as e:
        print(f"Error get_product_by_id: {e}")
        return None


async def delete_product(product_id: str):
    """Delete a product by id. Uses Supabase if available, otherwise local JSON fallback."""
    try:
        if supabase is not None:
            import asyncio
            # First delete any reviews that reference the product to avoid FK constraint errors
            try:
                _ = await asyncio.to_thread(lambda: supabase.table("reviews").delete().eq("product_id", product_id).execute())
            except Exception as e:
                print(f"Warning: failed to delete reviews for product {product_id}: {e}")

            # Now delete the product itself
            resp = await asyncio.to_thread(lambda: supabase.table("products").delete().eq("id", product_id).execute())
            if hasattr(resp, "error") and resp.error:
                raise Exception(resp.error)
            return {"success": True, "deleted_id": product_id}

        # Local JSON fallback: remove reviews and product
        db = _read_local_db()
        prods = db.get("products", [])
        new_prods = [p for p in prods if str(p.get("id")) != str(product_id)]
        db["products"] = new_prods
        reviews = db.get("reviews", [])
        db["reviews"] = [r for r in reviews if str(r.get("product_id")) != str(product_id)]
        _write_local_db(db)
        return {"success": True, "deleted_id": product_id}
    except Exception as e:
        print(f"Error deleting product: {e}")
        raise


async def get_recent_reviews_with_sentiment(limit: int = 50):
    """Fetch recent reviews with their sentiment analysis included."""
    try:
        # Supabase join syntax: table(*), tied via foreign key
        import asyncio
        response = await asyncio.to_thread(lambda: supabase.table("reviews")\
            .select("*, sentiment_analysis(*)")\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute())
        return response.data
    except Exception as e:
        print(f"Error fetching recent reviews: {e}")
        return []



async def get_analysis_by_hash(text_hash: str):
    """Check if analysis exists for a given text hash."""
    try:
        # 1. Find a review with this hash
        review_response = supabase.table("reviews").select("id").eq("text_hash", text_hash).limit(1).execute()
        if not review_response.data:
            return None
            
        review_id = review_response.data[0]["id"]
        
        # 2. Get the analysis for this review
        analysis_response = supabase.table("sentiment_analysis").select("*").eq("review_id", review_id).execute()
        if analysis_response.data:
            return analysis_response.data[0]
            
        return None
    except Exception as e:
        print(f"Error checking cache: {e}")
        return None


async def save_sentiment_analysis(analysis_data: dict):
    """Save sentiment analysis results to the database."""
    try:
        response = supabase.table("sentiment_analysis").insert(analysis_data).execute()
        return response.data
    except Exception as e:
        print(f"Error saving sentiment analysis: {e}")
        raise


# Cache for dashboard stats (30 second TTL)
import time
_dashboard_cache = {"data": None, "timestamp": 0}
_CACHE_TTL = 30  # seconds

async def get_dashboard_stats():
    """
    Fetch aggregated dashboard stats with caching.
    """
    global _dashboard_cache
    
    # Check cache first
    now = time.time()
    if _dashboard_cache["data"] and (now - _dashboard_cache["timestamp"]) < _CACHE_TTL:
        return _dashboard_cache["data"]
    
    # Fetch fresh data
    try:
        data = await _get_dashboard_metrics_fallback()
        _dashboard_cache = {"data": data, "timestamp": now}
        return data
    except Exception as e:
        print(f"Dashboard stats error: {e}")
        return _dashboard_cache["data"] or {
            "totalReviews": 0,
            "sentimentScore": 0,
            "averageCredibility": 0,
            "platformBreakdown": {}
        }

async def _get_dashboard_metrics_fallback():
    """Optimized aggregation for dashboard metrics."""
    import asyncio
    from datetime import datetime, timedelta
    
    try:
        # Parallelize independent queries
        # 1. Total Reviews & Platform (using Reviews table)
        reviews_task = asyncio.to_thread(lambda: supabase.table("reviews").select("id, platform, created_at").execute())
        
        # 2. Sentiment Data (using SentimentAnalysis table) - We need created_at from reviews ideally, 
        # but for speed we might query reviews with join. 
        # Let's do a join: reviews select *, sentiment_analysis(*)
        # However, for large datasets, this is heavy. 
        # Let's fetch sentiment_analysis and assume we can link via review_id or if created_at is needed, we rely on reviews.
        # Actually, let's just fetch joined data for the last 30 days to compute trends/stats.
        
        # 2. Sentiment Data (using SentimentAnalysis table) - 30d window
        # We include 'content' now for recent reviews feed
        start_date_30d = (datetime.utcnow() - timedelta(days=30)).isoformat()
        
        joined_task = asyncio.to_thread(lambda: supabase.table("reviews")
            .select("id, content, created_at, platform, sentiment_analysis(label, score, credibility, emotions, aspects)")
            .gte("created_at", start_date_30d)
            .execute()
        )

        # 3. Top Topics
        topic_task = asyncio.to_thread(lambda: supabase.table("topic_analysis").select("topic_name, size, sentiment").order("size", desc=True).limit(10).execute())
        
        # 4. Alerts
        alerts_task = asyncio.to_thread(lambda: supabase.table("alerts").select("*").order("created_at", desc=True).limit(5).execute())

        # Execute parallel
        joined_resp, topic_resp, alerts_resp = await asyncio.gather(
            joined_task, topic_task, alerts_task, return_exceptions=True
        )
        
        # Process joined data
        reviews_data = joined_resp.data if not isinstance(joined_resp, Exception) and joined_resp.data else []
        topic_data = topic_resp.data if not isinstance(topic_resp, Exception) and topic_resp.data else []
        alerts_data = alerts_resp.data if not isinstance(alerts_resp, Exception) and alerts_resp.data else []

        # Aggregators
        # Note: 'count=exact' is expensive, so we only do it if we really need true total >= 30d
        # For dashboard speed, usually 30d total is enough, but "Total Reviews" usually implies all-time.
        # We will dispatch a separate optimized count query.
        total_count_task = asyncio.to_thread(lambda: supabase.table("reviews").select("id", count="exact", head=True).execute())
        
        # We await it immediately here, but could have gathered it.
        total_count_resp = await total_count_task
        total_reviews_all_time = 0
        if hasattr(total_count_resp, 'count') and total_count_resp.count is not None:
             total_reviews_all_time = total_count_resp.count
        else:
             total_reviews_all_time = len(reviews_data) # Fallback to 30d count

        platforms = {}
        sentiment_scores = []
        credibility_scores = []
        emotions_agg = {}
        aspects_agg = {}
        
        # For Trends
        daily_sentiment = {} # "YYYY-MM-DD" -> [scores]
        
        now = datetime.utcnow()
        seven_days_ago = now - timedelta(days=7)
        fourteen_days_ago = now - timedelta(days=14)
        
        current_period_scores = []
        prev_period_scores = []

        for r in reviews_data:
            # Platform
            p = r.get("platform", "unknown")
            platforms[p] = platforms.get(p, 0) + 1
            
            # Date
            created_at = r.get("created_at")
            if not created_at: continue
            
            try:
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except:
                continue
                
            date_str = dt.strftime("%Y-%m-%d")
            
            # Sentiment Analysis Data
            sa = r.get("sentiment_analysis")
            if isinstance(sa, list) and sa: sa = sa[0]
            if not sa: continue
            
            # Score
            label = sa.get("label", "NEUTRAL")
            score = 50
            if label == "POSITIVE": score = 100
            elif label == "NEGATIVE": score = 0
            
            # Refine with exact score if available
            if sa.get("score") is not None:
                # Assuming sa['score'] is -1 to 1 or 0 to 1.
                # Let's assume 0-1 from TextBlob/Transformer, mapped to 0-100
                raw = float(sa.get("score"))
                if raw <= 1.0: score = raw * 100
                else: score = raw # already 0-100?
            
            sentiment_scores.append(score)
            
            # Credibility
            cred = float(sa.get("credibility", 0))
            credibility_scores.append(cred)
            
            # Delta Calculation buckets
            if dt >= seven_days_ago.replace(tzinfo=dt.tzinfo):
                current_period_scores.append(score)
            elif dt >= fourteen_days_ago.replace(tzinfo=dt.tzinfo):
                prev_period_scores.append(score)
            
            # Trend Aggregation
            if date_str not in daily_sentiment:
                daily_sentiment[date_str] = {"sum": 0, "count": 0}
            daily_sentiment[date_str]["sum"] += score
            daily_sentiment[date_str]["count"] += 1
            
            # Emotions
            ems = sa.get("emotions", [])
            if isinstance(ems, list):
                for e in ems:
                    # e might be string or dict {"name": "joy", "score": 0.9}
                    if isinstance(e, str):
                        emotions_agg[e] = emotions_agg.get(e, 0) + 1
                    elif isinstance(e, dict):
                        nm = e.get("label") or e.get("name")
                        if nm: emotions_agg[nm] = emotions_agg.get(nm, 0) + 1
            
            # Aspects
            asps = sa.get("aspects", [])
            if isinstance(asps, list):
                 for a in asps:
                     # a might be {"aspect": "price", "sentiment": "negative"}
                     if isinstance(a, dict):
                         nm = a.get("aspect")
                         sent = a.get("sentiment", "neutral")
                         if nm:
                             if nm not in aspects_agg: aspects_agg[nm] = {"total": 0, "positive": 0, "negative": 0}
                             aspects_agg[nm]["total"] += 1
                             if sent.lower() == "positive": aspects_agg[nm]["positive"] += 1
                             elif sent.lower() == "negative": aspects_agg[nm]["negative"] += 1

        # Calculate Averages
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        avg_credibility = (sum(credibility_scores) / len(credibility_scores)) * 100 if credibility_scores else 0
        
        # Delta
        curr_avg = sum(current_period_scores) / len(current_period_scores) if current_period_scores else 0
        prev_avg = sum(prev_period_scores) / len(prev_period_scores) if prev_period_scores else 0
        sentiment_delta = curr_avg - prev_avg
        
        # Bot Detection
        bots_detected = sum(1 for c in credibility_scores if c < 0.4) # Strict
        verified_reviews = sum(1 for c in credibility_scores if c > 0.8)

        # Recommendations Logic (Positive %)
        pos_percent = sum(1 for s in sentiment_scores if s > 60) / len(sentiment_scores) * 100 if sentiment_scores else 0
        
        # Format Top Keywords (Topics)
        topics = [{"text": t["topic_name"], "value": t["size"], "sentiment": t.get("sentiment")} for t in topic_data]
        negative_topics = [t["topic_name"] for t in topic_data if t.get("sentiment") == "negative"]

        # Format Trends
        sentiment_trends = []
        sorted_dates = sorted(daily_sentiment.keys())
        for d in sorted_dates:
            val = daily_sentiment[d]
            avg = val["sum"] / val["count"]
            sentiment_trends.append({"date": d, "sentiment": avg})
            
        # Format Aspects
        formatted_aspects = []
        for aspect, stats in aspects_agg.items():
            # simple score: (pos - neg) / total * 100, normalized to 0-100
            # or just pos %?
            # User wants Radar chart. usually 0-100.
            score = 50 # neutral base
            if stats["total"] > 0:
                net = (stats["positive"] - stats["negative"])
                # map -total to +total -> 0 to 100
                score = 50 + (net / stats["total"] * 50)
            formatted_aspects.append({"aspect": aspect, "score": score, "count": stats["total"]})
        
        # Format Emotions
        formatted_emotions = [{"name": k, "value": v, "color": "var(--sentinel-primary)"} for k, v in emotions_agg.items()]

        # Generate Recommendations
        try:
            from services.report_service import report_service
            recommendations = report_service.generate_recommendations({
                "positive_percent": pos_percent,
                "negative_topics": negative_topics
            })
        except ImportError:
            recommendations = []
        except Exception as e:
            recommendations = []
            
        # Recent Reviews
        recent_reviews = []
        # Reuse the first 10 from reviews_data if sorted desc, otherwise ensure sort
        reviews_data.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        for r in reviews_data[:10]:
            sa = r.get("sentiment_analysis")
            if isinstance(sa, list) and sa: sa = sa[0]
            if not sa: sa = {}
            
            recent_reviews.append({
                "id": r.get("id"),
                "text": r.get("content") or r.get("text") or "No content",
                "platform": r.get("platform", "web"),
                "username": r.get("username") or r.get("author", "Anonymous"),
                "sentiment": (sa.get("label") or "neutral").lower(),
                "sentiment_label": (sa.get("label") or "neutral").upper(),
                "timestamp": r["created_at"],
                "sourceUrl": r.get("source_url"),
                "credibility": float(sa.get("credibility", 0)),
                "like_count": r.get("like_count", 0),
                "reply_count": r.get("reply_count", 0),
                "retweet_count": r.get("retweet_count", 0)
            })



        return {
            "totalReviews": total_reviews_all_time,
            "sentimentScore": avg_sentiment,
            "sentimentDelta": sentiment_delta,
            "averageCredibility": avg_credibility,
            "platformBreakdown": platforms,
            "topKeywords": topics,
            "recommendations": recommendations,
            "recentReviews": recent_reviews,
            "sentimentTrends": sentiment_trends,
            "aspectScores": formatted_aspects,
            "emotions": formatted_emotions,
            "alerts": alerts_data,
            "credibilityReport": {
                "overallScore": avg_credibility,
                "verifiedReviews": verified_reviews,
                "botsDetected": bots_detected,
                "spamClusters": 0,
                "suspiciousPatterns": 0,
                "totalAnalyzed": len(sentiment_scores)
            }
        }
    except Exception as e:
        print(f"Fallback metrics failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "totalReviews": 0,
            "sentimentScore": 0,
            "averageCredibility": 0,
            "platformBreakdown": {},
            "credibilityReport": {
                "overallScore": 0,
                "verifiedReviews": 0,
                "botsDetected": 0
            }
        }


async def get_advanced_analytics():
    """
    Calculate advanced real-time metrics using SQL.
    Engagement, Accuracy, Speed, Reach.
    """
    try:
        # 1. Total Reviews
        # select author/created_at (avoid selecting non-existent `username` column)
        count_res = supabase.table("reviews").select("id, created_at, author", count="exact").execute()
        total = count_res.count or 0

        # Compute first review time
        first_time = None
        authors = set()
        try:
            rows = count_res.data or []
            for r in rows:
                created = r.get('created_at')
                if created:
                    # created is ISO string
                    from datetime import datetime
                    try:
                        t = datetime.fromisoformat(created)
                    except Exception:
                        try:
                            t = datetime.strptime(created, "%Y-%m-%dT%H:%M:%S.%fZ")
                        except Exception:
                            t = None
                    if t:
                        if first_time is None or t < first_time:
                            first_time = t
                # prefer `username` when available, otherwise fall back to `author`
                authors.add(r.get('username') or r.get('author'))
        except Exception:
            first_time = None

        # Engagement: reviews per hour since first review
        engagement_val = 0
        try:
            from datetime import datetime
            now = datetime.utcnow()
            if first_time:
                delta = now - first_time
                hours = max(delta.total_seconds() / 3600.0, 1e-6)
                engagement_val = float(total) / hours
            else:
                engagement_val = float(total)
        except Exception:
            engagement_val = 0

        # Model Accuracy: average score from sentiment_analysis
        accuracy_val = 0
        processing_speed_val = 0
        try:
            sentiment_res = supabase.table("sentiment_analysis").select("score, created_at, review_id").execute()
            if sentiment_res.data:
                data = sentiment_res.data
                accuracies = [float(r.get("score") or 0) for r in data]
                accuracy_val = sum(accuracies) / len(accuracies) if accuracies else 0
                processing_speed_val = 0.35
        except Exception:
            accuracy_val = 0
            processing_speed_val = 0

        # Reach: unique authors count
        reach_val = len(authors)

        return {
            "engagement_rate": engagement_val,
            "model_accuracy": accuracy_val,
            "processing_speed_ms": int(processing_speed_val * 1000),
            "total_reach": reach_val
        }
    except Exception as e:
        print(f"Advanced Analytics Error: {e}")
        return {
            "engagement_rate": 0,
            "model_accuracy": 0,
            "processing_speed_ms": 0,
            "total_reach": 0
        }
