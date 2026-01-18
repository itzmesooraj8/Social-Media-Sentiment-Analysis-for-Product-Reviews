"""
Production-ready FastAPI app for Phase 1.

Endpoints:
- GET /api/products
- POST /api/products
- GET /api/reviews
- POST /api/scrape/trigger
- GET /api/dashboard

Focus: YouTube scraping + sentiment analysis. Reddit/Twitter are stubbed and deferred.
"""

import os
import sys
import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent))

from services.ai_service import ai_service
from services.scrapers import run_all_scrapers
from database import supabase, get_products, add_product, get_reviews, get_dashboard_stats

app = FastAPI(title="Sentiment Beacon API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProductCreate(BaseModel):
    name: str
    keywords: Optional[List[str]] = []
    track_reddit: Optional[bool] = False
    track_twitter: Optional[bool] = False
    track_youtube: Optional[bool] = True


class ScrapeTrigger(BaseModel):
    product_id: str


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/products")
async def api_get_products():
    products = await get_products()
    return {"success": True, "data": products}


@app.post("/api/products")
async def api_create_product(payload: ProductCreate):
    data = {"name": payload.name, "keywords": payload.keywords or [],
            "track_reddit": payload.track_reddit, "track_twitter": payload.track_twitter,
            "track_youtube": payload.track_youtube}
    res = await add_product(data)
    return {"success": True, "data": res}


@app.get("/api/reviews")
async def api_get_reviews(product_id: Optional[str] = None, platform: Optional[str] = None, limit: int = 100):
    try:
        query = supabase.table("reviews").select("*")
        if product_id:
            query = query.eq("product_id", product_id)
        if platform:
            query = query.eq("platform", platform)
        resp = query.order("created_at", desc=True).limit(limit).execute()
        return {"success": True, "data": resp.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scrape/trigger")
async def api_scrape_trigger(payload: ScrapeTrigger):
    """Trigger scraping for a product_id. Runs YouTube scraper (and stubs for others) in parallel.

    Steps:
    - Fetch product and keywords
    - Run scrapers in parallel
    - Analyze fetched items with ai_service
    - Upsert into `reviews` table
    - Return count of new reviews
    """
    product_id = payload.product_id
    if not product_id:
        raise HTTPException(status_code=400, detail="product_id required")

    # Fetch product
    try:
        prod_resp = supabase.table("products").select("*").eq("id", product_id).limit(1).execute()
        if not prod_resp.data:
            raise HTTPException(status_code=404, detail="Product not found")
        product = prod_resp.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    keywords = product.get("keywords") or []
    if not keywords:
        # default to product name
        keywords = [product.get("name")]

    # Run consolidated scrapers (YouTube + Reddit + Twitter) in parallel
    fetched_items = await run_all_scrapers(keywords, per_source=50)

    if not fetched_items:
        return {"success": True, "new": 0}

    # Analyze and prepare rows for insertion
    rows = []
    for it in fetched_items:
        content = it.get("content") or it.get("text") or ""
        # Run AI analysis in thread to avoid blocking (analyze_text is cached)
        analysis = await asyncio.to_thread(ai_service.analyze_text, content)
        row = {
            "product_id": product_id,
            "content": content,
            "platform": it.get("platform", "youtube"),
            "sentiment_score": float(analysis.get("score", 0.5)),
            "sentiment_label": analysis.get("label", "NEUTRAL"),
            "emotion": analysis.get("emotion", "neutral"),
            "credibility_score": float(analysis.get("credibility", it.get("credibility_score") or 0.5)),
            "source_url": it.get("source_url") or None,
            "created_at": it.get("created_at") or None,
        }
        rows.append(row)

    # Batch insert - ignore duplicates handling (Supabase upsert requires conflict key)
    try:
        insert_resp = supabase.table("reviews").insert(rows).execute()
        new_count = len(insert_resp.data) if insert_resp.data else 0
    except Exception as e:
        print(f"Insert error: {e}")
        new_count = 0

    return {"success": True, "new": new_count}


@app.get("/api/dashboard")
async def api_dashboard():
    # Use database helper which performs optimized queries and caching
    stats = await get_dashboard_stats()
    return {"success": True, "data": stats}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

