
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

