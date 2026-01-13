"""
FastAPI Backend Server for Sentiment Analysis Application
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.ai_service import ai_service
from services.reddit_scraper import reddit_scraper
from services.scheduler import start_scheduler
from services.data_pipeline import process_scraped_reviews
from auth.dependencies import verify_user
from database import (
    get_products,
    add_product,
    get_reviews,
    save_sentiment_analysis,
    get_dashboard_metrics,
    supabase
)


# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Sentiment Beacon API",
    description="Real-time sentiment analysis for social media reviews",
    version="1.0.0"
)

# Startup Event
@app.on_event("startup")
async def startup_event():
    """Start background services on app startup"""
    try:
        start_scheduler()
    except Exception as e:
        print(f"Failed to start scheduler: {e}")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic Models
class AnalyzeRequest(BaseModel):
    text: str


class ProductCreate(BaseModel):
    name: str
    sku: str
    category: str
    description: Optional[str] = None
    keywords: Optional[List[str]] = []


class ReviewCreate(BaseModel):
    product_id: str
    text: str
    platform: str
    source_url: Optional[str] = None


# Health Check
@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "Sentiment Beacon API is running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = "connected" if supabase else "disconnected"
    return {
        "status": "healthy",
        "database": db_status,
        "ai_service": "ready"
    }


# Sentiment Analysis Endpoints
@app.post("/api/analyze")
async def analyze_sentiment(request: AnalyzeRequest):
    """
    Analyze sentiment of a single text input.
    Returns sentiment label, score, emotions, and credibility.
    """
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        result = await ai_service.analyze_sentiment(request.text)
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# Product Endpoints
@app.get("/api/products")
async def list_products():
    """Get all products"""
    try:
        products = await get_products()
        return {
            "success": True,
            "data": products,
            "count": len(products)
        }
    except Exception as e:
    except Exception as e:
        print(f"Error fetching products: {e}")
        return {
            "success": True,
            "data": [],
            "count": 0
        }


@app.post("/api/products")
async def create_product(product: ProductCreate, user: dict = Depends(verify_user)):
    """Create a new product"""
    try:
        product_data = {
            "name": product.name,
            "sku": product.sku,
            "category": product.category,
            "description": product.description,
            "keywords": product.keywords,
            "status": "active"
        }
        
        result = await add_product(product_data)
        return {
            "success": True,
            "data": result,
            "message": "Product created successfully"
        }
    except Exception as e:
        print(f"Error creating product: {e}")
        # raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")
        return {
            "success": False,
            "message": f"Database error: {str(e)}" 
        }


@app.delete("/api/products/{product_id}")
async def delete_product(product_id: str, user: dict = Depends(verify_user)):
    """Delete a product"""
    try:
        supabase.table("products").delete().eq("id", product_id).execute()
        return {
            "success": True,
            "message": "Product deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete product: {str(e)}")


# Review Endpoints
@app.get("/api/reviews")
async def list_reviews(product_id: Optional[str] = None, limit: int = 100):
    """Get reviews, optionally filtered by product"""
    try:
        reviews = await get_reviews(product_id, limit)
        return {
            "success": True,
            "data": reviews,
            "count": len(reviews)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch reviews: {str(e)}")


@app.post("/api/reviews")
async def create_review(review: ReviewCreate):
    """Create a new review and analyze it"""
    try:
        # Analyze sentiment
        sentiment_result = await ai_service.analyze_sentiment(review.text)
        
        # Save review
        review_data = {
            "product_id": review.product_id,
            "text": review.text,
            "platform": review.platform,
            "source_url": review.source_url,
        }
        review_response = supabase.table("reviews").insert(review_data).execute()
        review_id = review_response.data[0]["id"] if review_response.data else None
        
        # Save sentiment analysis
        if review_id:
            analysis_data = {
                "review_id": review_id,
                "product_id": review.product_id,
                "label": sentiment_result.get("label"),
                "score": sentiment_result.get("score"),
                "emotions": sentiment_result.get("emotions", []),
                "credibility": sentiment_result.get("credibility", 0),
                "aspects": sentiment_result.get("aspects", [])
            }
            await save_sentiment_analysis(analysis_data)
        
        return {
            "success": True,
            "data": {
                "review": review_response.data[0] if review_response.data else None,
                "sentiment": sentiment_result
            },
            "message": "Review created and analyzed successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create review: {str(e)}")


# Dashboard Endpoints
@app.get("/api/dashboard")
async def get_dashboard():
    """Get dashboard metrics and data"""
    try:
        metrics = await get_dashboard_metrics()
        
        # Check if we have any data
        if metrics["totalReviews"] == 0:
            return {
                "success": True,
                "data": None  # Frontend will show empty state
            }
        
        # Get recent reviews with sentiment
        reviews = await get_reviews(limit=50)
        
        # Get sentiment trends
        sentiment_response = supabase.table("sentiment_analysis").select("*").limit(100).execute()
        # sentiment_data = sentiment_response.data # Not used in dashboard currently, handled by frontend sorting if needed
        
        return {
            "success": True,
            "data": {
                "metrics": metrics,
                "sentimentTrends": [], # Should be implemented with timeseries query
                "aspectScores": [],
                "alerts": [],
                "platformBreakdown": [],
                "topKeywords": [],
                "credibilityReport": {
                    "overallScore": metrics.get("averageCredibility", 0),
                    "botsDetected": metrics.get("botsDetected", 0),
                    "spamClusters": 0,
                    "suspiciousPatterns": 0,
                    "verifiedReviews": metrics.get("totalReviews", 0),
                    "totalAnalyzed": metrics.get("totalReviews", 0)
                },
                "lastUpdated": datetime.now().isoformat()
            }
        }
    except Exception as e:
    except Exception as e:
        print(f"Error fetching dashboard data: {e}")
        # Return empty data instead of crashing
        return {
            "success": True,
            "data": {
                "metrics": {
                    "totalReviews": 0,
                    "sentimentDelta": 0,
                    "botsDetected": 0,
                    "averageCredibility": 0
                },
                "sentimentTrends": [],
                "aspectScores": [],
                "alerts": [],
                "platformBreakdown": [],
                "topKeywords": [],
                "credibilityReport": {
                    "overallScore": 0,
                    "botsDetected": 0,
                    "spamClusters": 0,
                    "suspiciousPatterns": 0,
                    "verifiedReviews": 0,
                    "totalAnalyzed": 0
                },
                "lastUpdated": datetime.now().isoformat()
            }
        }


# Analytics Endpoints
@app.get("/api/analytics")
async def get_analytics():
    """Get analytics data"""
    try:
        # Fetch sentiment analysis data
        sentiment_response = supabase.table("sentiment_analysis").select("*").execute()
        sentiment_data = sentiment_response.data
        
        # Calculate platform breakdown
        reviews_response = supabase.table("reviews").select("platform").execute()
        reviews = reviews_response.data
        
        platform_counts = {}
        for review in reviews:
            platform = review.get("platform", "unknown")
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        return {
            "success": True,
            "data": {
                "sentimentData": sentiment_data,
                "platformBreakdown": platform_counts,
                "totalAnalyzed": len(sentiment_data)
            }
        }
    except Exception as e:
    except Exception as e:
        print(f"Error fetching analytics: {e}")
        # Return empty structure instead of crashing
        return {
            "success": True, 
            "data": {
                "sentimentData": [],
                "platformBreakdown": {},
                "totalAnalyzed": 0
            }
        }


# Integration Endpoints
@app.get("/api/integrations")
async def get_integrations():
    """Get API integration status"""
    try:
        response = supabase.table("integrations").select("*").execute()
        return {
            "success": True,
            "data": response.data
        }
    except Exception as e:
        # Return empty if table doesn't exist yet
        return {
            "success": True,
            "data": []
        }

# Reddit Scraping Endpoint
@app.post("/api/scrape/reddit")
async def scrape_reddit(product_id: str, product_name: str, subreddits: Optional[List[str]] = None, user: dict = Depends(verify_user)):
    """Scrape Reddit for product mentions"""
    try:
        if subreddits is None:
            subreddits = ['all']
        
        # Scrape Reddit
        reviews = await reddit_scraper.search_product_mentions(product_name, subreddits, limit=50)
        
        if not reviews:
            return {
                "success": True,
                "message": "No reviews found",
                "count": 0
            }
        
        # Process reviews using reusable pipeline
        saved_count = await process_scraped_reviews(product_id, reviews)
        
        return {
            "success": True,
            "message": f"Scraped and analyzed {saved_count} reviews",
            "count": saved_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
