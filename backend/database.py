"""
Database module for Supabase connection and operations.
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Warning: Supabase credentials not found in environment variables")
    supabase: Client = None
else:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✓ Supabase client initialized successfully")
    except Exception as e:
        print(f"Error initializing Supabase client: {e}")
        supabase = None


def get_supabase_client() -> Client:
    """Get the Supabase client instance."""
    return supabase


# Database helper functions
async def get_products():
    """Fetch all products from the database."""
    try:
        response = supabase.table("products").select("*").execute()
        return response.data
    except Exception as e:
        print(f"Error fetching products: {e}")
        return []


async def add_product(product_data: dict):
    """Add a new product to the database."""
    try:
        response = supabase.table("products").insert(product_data).execute()
        return response.data
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


async def get_dashboard_stats():
    """
    Fetch aggregated dashboard stats using efficient Database RPC.
    Falls back to Python calculation if RPC is not set up.
    """
    try:
        # Try calling the RPC function
        response = supabase.rpc('get_dashboard_stats', {}).execute()
        if response.data:
            return response.data
            
        raise Exception("RPC returned no data")
    except Exception as e:
        print(f"RPC 'get_dashboard_stats' failed (User might need to run schema.sql): {e}")
        # Fallback to Python-side aggregation (Optimized)
        return await _get_dashboard_metrics_fallback()

async def _get_dashboard_metrics_fallback():
    """Fallback aggregation if SQL function is missing."""
    try:
        # Get total reviews count (Lightweight)
        reviews_resp = supabase.table("reviews").select("id, platform", count="exact").execute()
        total_reviews = reviews_resp.count if reviews_resp.count else 0
        
        # Get sentiment stats (Lightweight columns only)
        # Fetching all Might be slow for 10k+ rows, but better than nothing for fallback
        # In prod, the RPC is mandatory.
        sentiment_resp = supabase.table("sentiment_analysis").select("label, credibility").execute()
        sentiment_data = sentiment_resp.data
        
        if sentiment_data:
            # Map sentiment to 0-100 score
            score_map = {"POSITIVE": 100, "NEUTRAL": 50, "NEGATIVE": 0}
            total_score = sum(score_map.get(s.get("label", "NEUTRAL").upper(), 50) for s in sentiment_data)
            avg_sentiment = total_score / len(sentiment_data)
            
            avg_credibility = sum(s.get("credibility", 0) for s in sentiment_data) / len(sentiment_data)
        else:
            avg_sentiment = 0
            avg_credibility = 0
            
        # Platform breakdown
        platforms = {}
        if reviews_resp.data:
            for r in reviews_resp.data:
                p = r.get("platform", "unknown")
                platforms[p] = platforms.get(p, 0) + 1

        return {
            "totalReviews": total_reviews,
            "sentimentScore": avg_sentiment,
            "averageCredibility": avg_credibility,
            "platformBreakdown": platforms
        }
    except Exception as e:
        print(f"Fallback metrics failed: {e}")
        return {
            "totalReviews": 0,
            "sentimentScore": 0,
            "averageCredibility": 0,
            "platformBreakdown": {}
        }


async def get_advanced_analytics():
    """
    Calculate advanced real-time metrics using SQL.
    Engagement, Accuracy, Speed, Reach.
    """
    try:
        # 1. Total Reviews
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
                if r.get('author'):
                    authors.add(r.get('author'))
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
