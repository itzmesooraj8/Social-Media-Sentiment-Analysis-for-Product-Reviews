"""
FastAPI Backend Server - PRODUCTION MODE (No Mocks)
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

sys.path.insert(0, str(Path(__file__).parent))

from services.ai_service import ai_service
from services.reddit_scraper import reddit_scraper
from services.youtube_scraper import youtube_scraper
from services.url_processor import url_processor
from services.report_service import report_service
from services.scheduler import start_scheduler
from services.data_pipeline import process_scraped_reviews
from services.twitter_scraper import twitter_scraper
from auth.dependencies import get_current_user
from database import (
    get_products, add_product, get_reviews, get_recent_reviews_with_sentiment,
    save_sentiment_analysis, get_dashboard_stats, get_advanced_analytics, supabase
)

load_dotenv()

app = FastAPI(title="Sentiment Beacon API", version="1.0.0")

# Start Real-Time Scheduler
@app.on_event("startup")
async def startup_event():
    if os.environ.get("SKIP_SCHEDULER", "").lower() not in ["1", "true"]:
        start_scheduler()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Tighten this for final production deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Data Models ---
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

class ScrapeRequest(BaseModel):
    query: str
    product_id: Optional[str] = None

# --- Core Endpoints ---

@app.get("/health")
async def health_check():
    return {"status": "ok", "mode": "real-time"}

@app.post("/api/analyze")
async def analyze_sentiment(request: AnalyzeRequest, user: dict = Depends(get_current_user)):
    # Uses AI Service (HuggingFace/Local) - No heuristic fallback unless models fail completely
    result = await ai_service.analyze_sentiment(request.text)
    return {"success": True, "data": result}

@app.get("/api/products")
async def list_products(user: dict = Depends(get_current_user)):
    products = await get_products()
    return {"success": True, "data": products}

@app.post("/api/products")
async def create_product(product: ProductCreate, user: dict = Depends(get_current_user)):
    res = await add_product(product.dict())
    return {"success": True, "data": res}

@app.get("/api/dashboard")
async def get_dashboard(user: dict = Depends(get_current_user)):
    # Fetches REAL stats from DB
    stats = await get_dashboard_stats()
    adv = await get_advanced_analytics()
    
    # Merge for frontend
    data = {
        "metrics": {
            "totalReviews": stats.get("totalReviews", 0),
            "sentimentDelta": stats.get("sentimentScore", 0),
            "averageCredibility": stats.get("averageCredibility", 0),
            "engagementRate": adv.get("engagement_rate", 0)
        },
        "platformBreakdown": [], # Populate if your frontend needs it specifically formatted
        "recentReviews": []
    }
    
    # Get real recent reviews
    recent = await get_recent_reviews_with_sentiment(limit=10)
    data["recentReviews"] = recent
    
    return {"success": True, "data": data}

# --- Real-Time Scraping Endpoints ---

@app.post("/api/scrape/reddit")
async def scrape_reddit_endpoint(payload: ScrapeRequest, user: dict = Depends(get_current_user)):
    """Trigger real-time Reddit scrape"""
    if not payload.query:
        raise HTTPException(status_code=400, detail="Query required")
        
    print(f"Triggering Reddit scrape for: {payload.query}")
    reviews = await reddit_scraper.search_product_mentions(payload.query, limit=20)
    
    saved_count = 0
    if payload.product_id and reviews:
        saved_count = await process_scraped_reviews(payload.product_id, reviews)
        
    return {"success": True, "count": len(reviews), "saved": saved_count, "data": reviews}

@app.post("/api/scrape/twitter")
async def scrape_twitter_endpoint(payload: ScrapeRequest, user: dict = Depends(get_current_user)):
    """Trigger real-time Twitter scrape"""
    if not payload.query:
        raise HTTPException(status_code=400, detail="Query required")
        
    print(f"Triggering Twitter scrape for: {payload.query}")
    tweets = await twitter_scraper.search_tweets(payload.query, limit=20)
    
    saved_count = 0
    if payload.product_id and tweets:
        saved_count = await process_scraped_reviews(payload.product_id, tweets)
        
    return {"success": True, "count": len(tweets), "saved": saved_count, "data": tweets}

@app.post("/api/scrape/youtube")
async def scrape_youtube_endpoint(payload: ScrapeRequest, user: dict = Depends(get_current_user)):
    """Trigger real-time YouTube scrape"""
    if not payload.query:
        raise HTTPException(status_code=400, detail="Query required")
    
    reviews = youtube_scraper.search_video_comments(payload.query, max_results=50)
    
    saved_count = 0
    if payload.product_id and reviews:
        saved_count = await process_scraped_reviews(payload.product_id, reviews)
        
    return {"success": True, "count": len(reviews), "saved": saved_count}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
