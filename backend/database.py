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


async def get_dashboard_metrics():
    """Fetch aggregated metrics for the dashboard."""
    try:
        # Get total reviews count
        reviews_response = supabase.table("reviews").select("id", count="exact").execute()
        total_reviews = reviews_response.count if reviews_response.count else 0
        
        # Get sentiment analysis results
        sentiment_response = supabase.table("sentiment_analysis").select("*").limit(1000).execute()
        sentiment_data = sentiment_response.data
        
        # Calculate metrics
        if sentiment_data:
            positive_count = sum(1 for s in sentiment_data if s.get("label") == "POSITIVE")
            negative_count = sum(1 for s in sentiment_data if s.get("label") == "NEGATIVE")
            neutral_count = sum(1 for s in sentiment_data if s.get("label") == "NEUTRAL")
            
            total = len(sentiment_data)
            positive_pct = (positive_count / total * 100) if total > 0 else 0
            
            avg_credibility = sum(s.get("credibility", 0) for s in sentiment_data) / total if total > 0 else 0
        else:
            positive_pct = 0
            avg_credibility = 0
        
        return {
            "totalReviews": total_reviews,
            "sentimentDelta": positive_pct,
            "botsDetected": 0,  # Placeholder for now
            "averageCredibility": avg_credibility
        }
    except Exception as e:
        print(f"Error fetching dashboard metrics: {e}")
        return {
            "totalReviews": 0,
            "sentimentDelta": 0,
            "botsDetected": 0,
            "averageCredibility": 0
        }
