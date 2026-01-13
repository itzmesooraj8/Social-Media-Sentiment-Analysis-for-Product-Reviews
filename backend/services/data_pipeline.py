
from typing import List, Dict, Any
from database import supabase, save_sentiment_analysis
from services.ai_service import ai_service
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
            review_insert = {
                "product_id": product_id,
                "text": review_data['text'],
                "platform": review_data.get('platform', 'unknown'),
                "source_url": review_data.get('source_url'),
                "author": review_data.get('author')
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
                    "aspects": sentiment_result.get("aspects", [])
                }
                await save_sentiment_analysis(analysis_data)
                saved_count += 1
                
        except Exception as e:
            print(f"Error processing review: {e}")
            continue
            
    return saved_count
