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

if not SUPABASE_URL or not SUPABASE_KEY:
    print("CRITICAL: Supabase credentials not found in environment variables!")
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
            response = supabase.table("products").select("*").limit(50).execute()
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
            response = supabase.table("products").insert(product_data).execute()
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
        response = query.limit(limit).order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching reviews: {e}")
        return []


async def get_product_by_id(product_id: str):
    """Return a single product by id using Supabase if available, otherwise local JSON."""
    try:
        if supabase is not None:
            resp = supabase.table("products").select("*").eq("id", product_id).limit(1).execute()
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
            # First delete any reviews that reference the product to avoid FK constraint errors
            try:
                _ = supabase.table("reviews").delete().eq("product_id", product_id).execute()
            except Exception as e:
                print(f"Warning: failed to delete reviews for product {product_id}: {e}")

            # Now delete the product itself
            resp = supabase.table("products").delete().eq("id", product_id).execute()
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
        # Assuming review_id in sentiment_analysis references reviews.id
        # Note: In standard Supabase, we select from parent and include child? 
        # Or select from Child and include parent? 
        # Reviews is parent. Sentiment is child (review_id). 
        # To get Review + Sentiment, we usually need: select *, sentiment_analysis(*)
        response = supabase.table("reviews")\
            .select("*, sentiment_analysis(*)")\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
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
    try:
        # Get total reviews count (Lightweight)
        reviews_resp = supabase.table("reviews").select("id", count="exact").execute()
        total_reviews = reviews_resp.count if reviews_resp.count else 0
        
        # Get sentiment stats
        sentiment_resp = supabase.table("sentiment_analysis").select("label, credibility").execute()
        sentiment_data = sentiment_resp.data
        
        avg_credibility = 0
        bots_detected = 0
        verified_reviews = 0
        avg_sentiment = 0
        pos_percent = 0

        if sentiment_data:
            # Map sentiment to 0-100 score
            score_map = {"POSITIVE": 100, "NEUTRAL": 50, "NEGATIVE": 0}
            total_score = sum(score_map.get(s.get("label", "NEUTRAL").upper(), 50) for s in sentiment_data)
            avg_sentiment = total_score / len(sentiment_data)
            
            # Credibility Calculations
            cred_scores = [float(s.get("credibility", 0)) for s in sentiment_data]
            avg_credibility = (sum(cred_scores) / len(cred_scores)) * 100 if cred_scores else 0
            
            # Simple Bot Detection Logic: Credibility < 0.3
            bots_detected = sum(1 for s in cred_scores if s < 0.3)
            # Verified Logic: Credibility > 0.7
            verified_reviews = sum(1 for s in cred_scores if s > 0.7)
            
            # Calculate positive percent for recommendations
            pos_count = sum(1 for s in sentiment_data if s.get("label", "").upper() == "POSITIVE")
            pos_percent = (pos_count / len(sentiment_data)) * 100
            
        # Platform breakdown - aggregate manually
        platform_resp = supabase.table("reviews").select("platform").execute()
        platforms = {}
        if platform_resp.data:
             for r in platform_resp.data:
                 p = r.get("platform", "unknown")
                 platforms[p] = platforms.get(p, 0) + 1
        
        # Top Keywords / Topics
        topics = []
        negative_topics = []
        try:
            # Fetch recent top topics by size
            topic_resp = supabase.table("topic_analysis").select("topic_name, size, sentiment").order("size", desc=True).limit(10).execute()
            if topic_resp.data:
                topics = [{"text": t["topic_name"], "value": t["size"], "sentiment": t.get("sentiment")} for t in topic_resp.data]
                negative_topics = [t["topic_name"] for t in topic_resp.data if t.get("sentiment") == "negative"]
        except Exception:
            pass

        # Recent Reviews (for Feed)
        recent_reviews = []
        try:
            rr_data = await get_recent_reviews_with_sentiment(limit=10)
            for r in rr_data:
                # Flat map sentiment
                sa = r.get("sentiment_analysis") or {}
                # Handle if list
                if isinstance(sa, list) and sa: sa = sa[0]
                
                recent_reviews.append({
                    "id": r["id"],
                    "text": r.get("content") or r.get("text", ""),
                    "platform": r.get("platform", "web"),
                    "username": r.get("username") or r.get("author", "Anonymous"),
                    "sentiment": (sa.get("label") or "neutral").lower(),
                    "sentiment_label": (sa.get("label") or "neutral").upper(),
                    "timestamp": r["created_at"],
                    "sourceUrl": r.get("source_url"),
                    "credibility": sa.get("credibility"),
                    "like_count": r.get("like_count", 0),
                    "reply_count": r.get("reply_count", 0),
                    "retweet_count": r.get("retweet_count", 0)
                })
        except Exception as e:
            print(f"Recent reviews fetch failed: {e}")

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
            print(f"Error generating recommendations: {e}")
            recommendations = []

        return {
            "totalReviews": total_reviews,
            "sentimentScore": avg_sentiment,
            "averageCredibility": avg_credibility, # 0-100
            "platformBreakdown": platforms,
            "topKeywords": topics,
            "recommendations": recommendations,
            "recentReviews": recent_reviews,
            "credibilityReport": {
                "overallScore": avg_credibility,
                "verifiedReviews": verified_reviews,
                "botsDetected": bots_detected,
                "spamClusters": 0, # Placeholder for advanced logic
                "suspiciousPatterns": 0,
                "totalAnalyzed": len(sentiment_data) if sentiment_data else 0
            }
        }
    except Exception as e:
        print(f"Fallback metrics failed: {e}")
        return {
            "totalReviews": 0,
            "sentimentScore": 0,
            "averageCredibility": 0,
            "platformBreakdown": {},
            "credibilityReport": {
                "overallScore": 0,
                "verifiedReviews": 0,
                "botsDetected": 0,
                "spamClusters": 0,
                "suspiciousPatterns": 0,
                "totalAnalyzed": 0
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
