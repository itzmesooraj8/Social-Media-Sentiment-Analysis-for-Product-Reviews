"""
Simplified data pipeline used by the demo: save reviews and sentiment analysis
to Supabase. This implementation is defensive and compatible with the existing
`database.py` helpers (`supabase`, `save_sentiment_analysis`).
"""
from typing import List, Dict, Any
from database import supabase, save_sentiment_analysis
from services.ai_service import ai_service


async def save_reviews(reviews: List[Dict[str, Any]], product_id: str) -> int:
    """
    Save a list of review dicts to `reviews` table and their analyses to
    `sentiment_analysis`. Returns the count of saved reviews.
    Prioritizes `username` field falling back to `author` and finally 'Anonymous'.
    """
    if not reviews:
        return 0

    saved = 0
    for r in reviews:
        try:
            text = r.get("text") or r.get("content") or ""
            if not text or len(text) < 2:
                continue

            username = r.get("username") or r.get("author") or "Anonymous"

            review_obj = {
                "product_id": product_id,
                "text": text,
                "platform": r.get("platform") or "unknown",
                "username": username,
                "source_url": r.get("source_url") or r.get("url") or None,
            }

            resp = supabase.table("reviews").insert(review_obj).execute()
            if not resp or not resp.data:
                continue

            review_id = resp.data[0].get("id")

            # If sentiment already provided by upstream, save it; otherwise compute
            sentiment = r.get("sentiment")
            if not sentiment:
                try:
                    sentiment = await ai_service.analyze_sentiment(text)
                except Exception:
                    sentiment = {"label": "NEUTRAL", "score": 0.5}

            analysis = {
                "review_id": review_id,
                "product_id": product_id,
                "label": sentiment.get("label") if sentiment else None,
                "score": float(sentiment.get("score") or 0.0),
                "emotions": sentiment.get("emotions", []),
                "credibility": float(sentiment.get("credibility") or 0.0),
                "credibility_reasons": sentiment.get("credibility_reasons", []),
                "aspects": sentiment.get("aspects", []),
            }

            try:
                await save_sentiment_analysis(analysis)
            except Exception:
                # best-effort: continue even if saving analysis fails
                pass

            saved += 1

        except Exception:
            continue

    return saved


async def process_scraped_reviews(product_id: str, reviews: List[Dict[str, Any]]) -> int:
    """Compatibility wrapper used elsewhere in the codebase."""
    return await save_reviews(reviews, product_id)


__all__ = ["save_reviews", "process_scraped_reviews"]

from typing import List, Dict, Any
from database import supabase, save_sentiment_analysis
from services.ai_service import ai_service
from services.monitor_service import monitor_service
import asyncio

async def process_scraped_reviews(product_id: str, reviews: List[Dict[str, Any]]) -> int:
    """
    Process a list of scraped reviews: 
    1. Save to database
    2. Analyze sentiment
    3. Save analysis
    Returns count of successfully saved reviews.
    """
    saved_count = 0
    
    for review_data in reviews:
        try:
            # Check if review already exists (by source_url + product_id)
            # This is a naive check; ideally we'd have a unique constraint or index
            # But duplicate validation helps avoid processing the same Reddit post multiple times
            if review_data.get('source_url'):
                existing = supabase.table("reviews")\
                    .select("id")\
                    .eq("source_url", review_data['source_url'])\
                    .eq("product_id", product_id)\
                    .execute()
                if existing.data:
                    continue  # Skip duplicate

            # Save review
            import hashlib
            text_hash = hashlib.md5(review_data['text'].encode('utf-8')).hexdigest()

            # Persist caller-provided `username` when available, otherwise fall back to `author`
            review_insert = {
                "product_id": product_id,
                "text": review_data['text'],
                "platform": review_data.get('platform', 'unknown'),
                "source_url": review_data.get('source_url'),
                "username": review_data.get('username') or review_data.get('author'),
                "text_hash": text_hash
            }
            review_response = supabase.table("reviews").insert(review_insert).execute()
            
            if review_response.data:
                review_id = review_response.data[0]["id"]
                
                # Analyze sentiment
                sentiment_result = await ai_service.analyze_sentiment(review_data['text'])
                
                # Save analysis
                analysis_data = {
                    "review_id": review_id,
                    "product_id": product_id,
                    "label": sentiment_result.get("label"),
                    "score": sentiment_result.get("score"),
                    "emotions": sentiment_result.get("emotions", []),
                    "credibility": sentiment_result.get("credibility", 0),
                    "credibility_reasons": sentiment_result.get("credibility_reasons", []),
                    "aspects": sentiment_result.get("aspects", [])
                }
                await save_sentiment_analysis(analysis_data)
                saved_count += 1
                
                # Run monitor checks for this review (alerts, etc.)
                try:
                    # fire and forget
                    asyncio.create_task(monitor_service.evaluate_review(product_id, review_data, sentiment_result))
                except Exception as e:
                    print(f"Failed to schedule monitor evaluate: {e}")
                
        except Exception as e:
            print(f"Error processing review: {e}")
            continue
            
    # After processing batch, extract and save topics (best-effort)
    try:
        if saved_count > 0:
            await monitor_service.extract_and_save_topics(product_id, reviews)
    except Exception as e:
        print(f"Failed to extract/save topics: {e}")

    return saved_count

