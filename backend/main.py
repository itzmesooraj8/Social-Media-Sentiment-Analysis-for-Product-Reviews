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
from collections import defaultdict

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
    get_dashboard_stats,
    get_advanced_analytics,
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
            
            # Check for alerts based on the new review and analysis
            # We combine review data and analysis data for the check
            full_review_data = {**review_data, "analysis": analysis_data}
            await ai_service.check_for_alerts(full_review_data)
        
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
async def get_dashboard(user: dict = Depends(verify_user)):
    """Get dashboard metrics and data"""
    try:
        # Use optimized SQL/RPC stats
        metrics_raw = await get_dashboard_stats()
        
        metrics = {
             "totalReviews": metrics_raw.get("totalReviews", 0),
             "sentimentDelta": metrics_raw.get("sentimentScore", 0), # Mapping score to delta for frontend compat
             "botsDetected": 0,
             "averageCredibility": metrics_raw.get("averageCredibility", 0)
        }

        # --- Inject Advanced Analytics (Real Math) ---
        adv_stats = await get_advanced_analytics()
        metrics["engagementRate"] = adv_stats["engagement_rate"]
        metrics["modelAccuracy"] = adv_stats["model_accuracy"]
        metrics["processingSpeed"] = adv_stats["processing_speed_ms"]
        metrics["totalReach"] = adv_stats["total_reach"]
        
        # Check if we have any data
        if metrics["totalReviews"] == 0:
            return {
                "success": True,
                "data": None
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
        
        # Iterate over all recent reviews (or fetch more if needed) to build aggregates
        for r, fr in zip(raw_reviews, formatted_reviews):
            # Trends
            date_key = r.get("created_at", "")[:10] # YYYY-MM-DD
            sent = fr["sentiment"]
            trend_map[date_key][sent] += 1
            trend_map[date_key]["total"] += 1
            
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
            
        # Format Platforms (From RPC if available, or calc)
        platform_breakdown = []
        raw_platform_counts = metrics_raw.get("platformBreakdown", {})
        if raw_platform_counts:
             for plat, count in raw_platform_counts.items():
                  # We don't have sentiment per platform from RPC yet, defaulting to 0 breakdown
                  # Frontend Analytics chart handles 'total' correctly
                  platform_breakdown.append({
                      "platform": plat,
                      "total": count,
                      "positive": 0, "neutral": 0, "negative": 0
                  })
        else:
             # Fallback
             pass

            
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
async def get_analytics(user: dict = Depends(verify_user)):
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


# Alerts Endpoints
@app.get("/api/alerts")
async def list_alerts(user: dict = Depends(verify_user)):
    """Fetch alerts from DB; return empty list if none."""
    try:
        if not supabase:
            return {"success": True, "data": []}
        resp = supabase.table("alerts").select("*").order("created_at", desc=True).execute()
        data = resp.data or []
        return {"success": True, "data": data}
    except Exception as e:
        print(f"Error fetching alerts: {e}")
        return {"success": True, "data": []}


@app.post("/api/alerts/mark-read/{alert_id}")
async def mark_alert_read(alert_id: int, user: dict = Depends(verify_user)):
    try:
        if not supabase:
            raise HTTPException(status_code=500, detail="Database not configured")
        supabase.table("alerts").update({"is_read": True}).eq("id", alert_id).execute()
        return {"success": True, "message": "Marked read"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error marking alert read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Topics Analytics Endpoint
@app.get("/api/analytics/topics")
async def get_topic_clusters(limit: int = 100):
    """Fetch recent reviews and generate topic clusters using AI service."""
    try:
        reviews = await get_reviews(limit=limit)
        if not reviews:
            return {"success": True, "data": []}

        texts = [r.get("text", "") for r in reviews if r.get("text")]
        topics = await ai_service.generate_topic_clusters(texts)
        return {"success": True, "data": topics}
    except Exception as e:
        print(f"Topic cluster error: {e}")
        return {"success": True, "data": []}


# Settings Endpoints
@app.get("/api/settings")
async def get_settings(user_id: Optional[str] = None, user: dict = Depends(verify_user)):
    """Read settings from user_settings table. If user_id provided, filter by it."""
    try:
        if not supabase:
            return {"success": True, "data": []}
        query = supabase.table("user_settings").select("*")
        if user_id:
            query = query.eq("user_id", user_id)
        resp = query.execute()
        return {"success": True, "data": resp.data or []}
    except Exception as e:
        print(f"Error fetching settings: {e}")
        return {"success": True, "data": []}


@app.post("/api/settings")
async def post_settings(payload: Dict[str, Any], user: dict = Depends(verify_user)):
    """Upsert a user setting. Expects {user_id, key, value}."""
    try:
        if not supabase:
            raise HTTPException(status_code=500, detail="Database not configured")
        user_id = payload.get("user_id")
        key = payload.get("key")
        value = payload.get("value")
        if not user_id or not key:
            raise HTTPException(status_code=400, detail="user_id and key are required")
        # Upsert
        up = {"user_id": user_id, "key": key, "value": value}
        supabase.table("user_settings").upsert(up, on_conflict=["user_id", "key"]).execute()
        return {"success": True, "data": up}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error saving setting: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

# Import Endpoints
from fastapi import UploadFile, File, Form

@app.get("/api/reports/summary")
async def get_executive_summary(product_id: Optional[str] = None, user: dict = Depends(verify_user)):
    """Generate AI Executive Summary from recent negative feedback."""
    try:
        # Use report_service to generate a frequency-based summary from recent negative reviews
        summary = await report_service.generate_summary(limit=50)
        return {"success": True, "summary": summary}
    except Exception as e:
        print(f"Summary Error: {e}")
        return {"success": False, "summary": "Could not generate summary."}


@app.post("/api/import/csv")
async def import_csv(
    file: UploadFile = File(...),
    product_id: str = Form(...),
    platform: str = Form("twitter"),
    user: dict = Depends(verify_user)
):
    """Import reviews from CSV file"""
    try:
        from services.csv_import_service import csv_import_service
        contents = await file.read()
        result = await csv_import_service.process_csv(contents, product_id, platform)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


# Report Endpoints
class ReportRequest(BaseModel):
    type: str # 'sentiment', 'credibility'
    format: str # 'pdf', 'excel'
    date_range: Optional[Dict[str, str]] = None

@app.post("/api/reports/generate")
async def generate_report_endpoint(req: ReportRequest, user: dict = Depends(verify_user)):
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


@app.get("/api/products/compare")
async def compare_products(id_a: str, id_b: str):
    """Compare two products head-to-head"""
    try:
        # Helper to get stats
        async def get_product_stats(pid):
            # Fetch reviews + sentiment
            # This is heavy if many reviews, but okay for demo scale
            # Ideally fetch aggregating SQL
            reviews = await get_reviews(pid, limit=200) 
            if not reviews: return {"sentiment": 0, "credibility": 0, "count": 0, "aspects": {}}
            
            total_sent = 0
            total_cred = 0
            aspect_map = defaultdict(list)
            
            # We need sentiment analysis entries. 
            # get_reviews doesn't return analysis! `get_recent_reviews_with_sentiment` does but not filtered by ID.
            # We need `get_reviews_with_sentiment(product_id)`.
            # Let's adjust logic:
            # Query supabase manually
            response = supabase.table("reviews")\
                .select("*, sentiment_analysis(*)")\
                .eq("product_id", pid)\
                .limit(200)\
                .execute()
            
            data = response.data
            if not data: return {"sentiment": 0, "credibility": 0, "count": 0, "aspects": {}}
            
            count = len(data)
            for r in data:
                sent_entry = {}
                if r.get("sentiment_analysis") and isinstance(r["sentiment_analysis"], list) and len(r["sentiment_analysis"]) > 0:
                    sent_entry = r["sentiment_analysis"][0]
                
                label = sent_entry.get("label", "NEUTRAL")
                score = 50
                if label == "POSITIVE": score = 100
                elif label == "NEGATIVE": score = 0
                
                total_sent += score
                total_cred += float(sent_entry.get("credibility") or 0)
                
                for asp in sent_entry.get("aspects") or []:
                    ascore = 3
                    if asp["sentiment"] == "positive": ascore = 5
                    elif asp["sentiment"] == "negative": ascore = 1
                    aspect_map[asp["name"]].append(ascore)
            
            # Avg Aspect Scores
            final_aspects = {}
            for k, v in aspect_map.items():
                final_aspects[k] = sum(v)/len(v)
                
            return {
                "sentiment": total_sent / count,
                "credibility": total_cred / count,
                "count": count,
                "aspects": final_aspects
            }

        stats_a = await get_product_stats(id_a)
        stats_b = await get_product_stats(id_b)
        
        # Merge Aspects for Radar
        all_aspects = set(stats_a["aspects"].keys()) | set(stats_b["aspects"].keys())
        radar_data = []
        for aspect in all_aspects:
            radar_data.append({
                "subject": aspect,
                "A": stats_a["aspects"].get(aspect, 3), # Default neutral
                "B": stats_b["aspects"].get(aspect, 3),
                "fullMark": 5
            })
            
        # Sort by subject for consistency
        radar_data.sort(key=lambda x: x["subject"])
        
        return {
            "success": True,
            "data": {
                "aspects": radar_data,
                "metrics": {
                    "productA": {
                        "sentiment": stats_a["sentiment"],
                        "credibility": stats_a["credibility"],
                        "reviewCount": stats_a["count"]
                    },
                    "productB": {
                        "sentiment": stats_b["sentiment"],
                        "credibility": stats_b["credibility"],
                        "reviewCount": stats_b["count"]
                    }
                }
            }
        }
    except Exception as e:
        print(f"Comparison Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
