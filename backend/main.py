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
from services.youtube_scraper import youtube_scraper
from services.report_service import report_service
from services.scheduler import start_scheduler
from services.data_pipeline import process_scraped_reviews
from auth.dependencies import verify_user
from fastapi.responses import FileResponse, Response
from database import (
    get_products,
    add_product,
    get_reviews,
    get_recent_reviews_with_sentiment,
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

@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


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
        import hashlib
        text_hash = hashlib.md5(review.text.encode('utf-8')).hexdigest()
        
        review_data = {
            "product_id": review.product_id,
            "text": review.text,
            "platform": review.platform,
            "source_url": review.source_url,
            "text_hash": text_hash
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
                "credibility_reasons": sentiment_result.get("credibility_reasons", []),
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
        raw_reviews = await get_recent_reviews_with_sentiment(limit=50)
        formatted_reviews = []
        
        for r in raw_reviews:
            # Extract sentiment data if available
            # Supabase returns list for 1:Many, but here it's 1:1, usually data[0] if array
            sentiment_entry = {}
            if r.get("sentiment_analysis") and isinstance(r["sentiment_analysis"], list) and len(r["sentiment_analysis"]) > 0:
                sentiment_entry = r["sentiment_analysis"][0]
            elif r.get("sentiment_analysis") and isinstance(r["sentiment_analysis"], dict):
                sentiment_entry = r["sentiment_analysis"]
                
            formatted_reviews.append({
                "id": r.get("id"),
                "platform": r.get("platform", "forums"), # Default to forums if missing
                "username": r.get("author") or r.get("username") or "Anonymous",
                "text": r.get("text", ""),
                "sentiment": (sentiment_entry.get("label") or "NEUTRAL").lower(),
                "credibility": float(sentiment_entry.get("credibility") or 0),
                "credibilityReasons": sentiment_entry.get("credibility_reasons") or [],
                "sourceUrl": r.get("source_url"),
                "timestamp": r.get("created_at"),
                "likes": 0,
                "aspects": sentiment_entry.get("aspects") or [],
                "isBot": False 
            })

        # --- Aggregate Real Data for Widgets ---
        
        # 1. Sentiment Trend (Daily)
        # In a real app, use Supabase .rpc() or date_trunc. Here we aggregate in python for simplicity.
        # Group by Date
        from collections import defaultdict
        trend_map = defaultdict(lambda: {"positive": 0, "neutral": 0, "negative": 0, "total": 0})
        
        # 2. Aspect Scores
        aspect_map = defaultdict(list)
        
        # 3. Emotions
        emotion_counts = defaultdict(int)
        
        # 4. Platform Breakdown
        platform_counts = defaultdict(lambda: {"positive": 0, "neutral": 0, "negative": 0, "total": 0})
        
        # Iterate over all recent reviews (or fetch more if needed) to build aggregates
        # ideally fetch a larger set for stats, but we'll use the 50 fetched + maybe a separate query for global stats
        # For Demo: using the recent 50 reviews to populate charts is often enough to show "live" movement
        
        for r, fr in zip(raw_reviews, formatted_reviews):
            # Trends
            date_key = r.get("created_at", "")[:10] # YYYY-MM-DD
            sent = fr["sentiment"]
            trend_map[date_key][sent] += 1
            trend_map[date_key]["total"] += 1
            
            # Platforms
            plat = fr["platform"]
            platform_counts[plat][sent] += 1
            platform_counts[plat]["total"] += 1
            
            # Aspects
            for asp in fr["aspects"]:
                score = 3 # neutral default
                if asp["sentiment"] == "positive": score = 5
                elif asp["sentiment"] == "negative": score = 1
                aspect_map[asp["name"]].append(score)
                
            # Emotions (Parsing from analysis)
            sentiment_entry = {}
            if r.get("sentiment_analysis") and isinstance(r["sentiment_analysis"], list) and len(r["sentiment_analysis"]) > 0:
                sentiment_entry = r["sentiment_analysis"][0]
            emotions = sentiment_entry.get("emotions", [])
            for agg in emotions:
                if agg.get("score", 0) > 0.3: # Threshold
                    emotion_counts[agg["name"]] += 1

        # Format Trends
        sentiment_trends = []
        for date, counts in sorted(trend_map.items()):
            sentiment_trends.append({
                "date": date,
                **counts
            })
            
        # Format Aspects
        aspect_scores = []
        for name, scores in aspect_map.items():
            avg = sum(scores) / len(scores)
            label = "neutral"
            if avg > 3.5: label = "positive"
            if avg < 2.5: label = "negative"
            aspect_scores.append({
                "aspect": name,
                "score": avg,
                "sentiment": label,
                "reviewCount": len(scores)
            })
            
        # Format Platforms
        platform_breakdown = []
        for plat, counts in platform_counts.items():
            platform_breakdown.append({
                "platform": plat,
                **counts
            })
            
        # Format Keywords (Simple frequency from text)
        # Real impl needs NLP keyword extraction
        from collections import Counter
        all_text = " ".join([r.get("text", "") for r in raw_reviews])
        words = [w.lower() for w in all_text.split() if len(w) > 4]
        common = Counter(words).most_common(10)
        top_keywords = [{"word": w, "count": c, "sentiment": "neutral", "trend": "stable"} for w, c in common]

        return {
            "success": True,
            "data": {
                "metrics": metrics,
                "sentimentTrends": sentiment_trends, 
                "aspectScores": aspect_scores,
                "alerts": [], # Alerts still mock till we implement alert logic tab
                "platformBreakdown": platform_breakdown,
                "topKeywords": top_keywords,
                "credibilityReport": {
                    "overallScore": metrics.get("averageCredibility", 0),
                    "botsDetected": metrics.get("botsDetected", 0),
                    "spamClusters": 0,
                    "suspiciousPatterns": 0,
                    "verifiedReviews": metrics.get("totalReviews", 0),
                    "totalAnalyzed": metrics.get("totalReviews", 0)
                },
                "recentReviews": formatted_reviews,
                "lastUpdated": datetime.now().isoformat()
            }
        }
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


# YouTube Scraping Endpoint
@app.post("/api/scrape/youtube")
async def scrape_youtube_endpoint(product_id: str, query: str, user: dict = Depends(verify_user)):
    """Scrape YouTube comments"""
    try:
        # Scrape
        reviews = youtube_scraper.search_video_comments(query, max_results=50)
        
        if not reviews:
            return {"success": True, "message": "No comments found", "count": 0}
            
        saved_count = await process_scraped_reviews(product_id, reviews)
        return {"success": True, "message": f"Scraped {saved_count} YouTube comments", "count": saved_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"YouTube Scrape Failed: {str(e)}")


# Report Endpoints
class ReportRequest(BaseModel):
    type: str # 'sentiment', 'credibility'
    format: str # 'pdf', 'excel'
    date_range: Optional[Dict[str, str]] = None

@app.post("/api/reports/generate")
async def generate_report_endpoint(req: ReportRequest):
    try:
         result = await report_service.generate_report(req.type, req.format)
         # Return metadata, clean way is to return URL or ID. For simplicity, we return filename and content in a downloadable way?
         # No, REST API usually returns URL or binary. 
         # Let's save to disk temporarily and return link, OR return base64. 
         # A simpler approach for this demo: Return params to trigger a GET download
         # Actually, we can just return the content directly if it's a small file, or save to 'generated_reports'
         
         out_dir = "generated_reports"
         os.makedirs(out_dir, exist_ok=True)
         filepath = os.path.join(out_dir, result["filename"])
         
         with open(filepath, "wb") as f:
             f.write(result["content"])
             
         return {
             "success": True, 
             "filename": result["filename"], 
             "downloadUrl": f"/api/reports/download/{result['filename']}"
         }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report Generation Failed: {str(e)}")

@app.get("/api/reports/download/{filename}")
async def download_report(filename: str):
    file_path = os.path.join("generated_reports", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename)
    raise HTTPException(status_code=404, detail="Report not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
