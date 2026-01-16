import hashlib
import json
from typing import List, Dict, Any
from datetime import datetime
from database import supabase  # Use the shared client

class DataPipelineService:
    async def process_reviews(self, reviews: List[Dict[str, Any]], product_id: str) -> List[Dict[str, Any]]:
        """
        Cleaning, Sentiment Analysis, and Saving to DB (Crash-Proof Version)
        """
        if not reviews:
            return []

        processed_reviews = []
        
        # 1. Prepare Data
        for review in reviews:
            # Generate a unique hash to prevent duplicates
            content = review.get("text") or review.get("content", "")
            if not content:
                continue
                
            text_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            # Basic Sentiment (Fallback if AI service fails)
            # You can plug in your advanced model here
            sentiment_score = 0.0
            sentiment_label = "neutral"
            blob = content.lower()
            if any(w in blob for w in ["great", "amazing", "love", "best", "good"]):
                sentiment_score = 0.8
                sentiment_label = "positive"
            elif any(w in blob for w in ["bad", "hate", "worst", "slow", "broken"]):
                sentiment_score = -0.6
                sentiment_label = "negative"

            processed_reviews.append({
                "product_id": product_id,
                "text": content,  # We use 'text' as the standard
                "username": review.get("author") or review.get("username", "Anonymous"),
                "platform": review.get("platform", "web_upload"),
                "source_url": review.get("source_url", ""),
                "text_hash": text_hash,
                "sentiment_score": sentiment_score,
                "sentiment_label": sentiment_label,
                "credibility_score": 0.95, # Mock credibility for demo
                "created_at": review.get("created_at") or datetime.now().isoformat()
            })

        # 2. Save to Database (The Robust Part)
        saved_count = 0
        for row in processed_reviews:
            try:
                # Try inserting everything
                data_to_save = {
                    "product_id": row["product_id"],
                    "content": row["text"], # Map 'text' to 'content' for legacy DB support
                    "text": row["text"],    # Also save as 'text' if column exists
                    "author": row["username"],
                    "username": row["username"],
                    "platform": row["platform"],
                    "source_url": row["source_url"],
                    "sentiment_score": row["sentiment_score"],
                    "sentiment_label": row["sentiment_label"],
                    "credibility_score": row["credibility_score"],
                    "text_hash": row["text_hash"],
                    "created_at": row["created_at"]
                }
                
                # Attempt save
                supabase.table("reviews").insert(data_to_save).execute()
                saved_count += 1
                
            except Exception as e:
                err = str(e)
                # SELF-HEALING LOGIC:
                # If DB complains about missing columns, remove them and retry!
                retry_data = data_to_save.copy()
                
                if "text_hash" in err:
                    del retry_data["text_hash"]
                if "username" in err:
                    del retry_data["username"]
                if "text" in err and "content" in retry_data:
                    del retry_data["text"] # Fallback to 'content' only
                
                try:
                    # Retry with safer data
                    supabase.table("reviews").insert(retry_data).execute()
                    saved_count += 1
                    print(f"   ⚠️ Saved review with reduced fields (Schema mismatch handled).")
                except Exception as final_error:
                    print(f"   ❌ Final Save Error: {final_error}")

        print(f"✅ Data Pipeline: Successfully saved {saved_count}/{len(processed_reviews)} reviews.")
        return processed_reviews

data_pipeline = DataPipelineService()

async def process_scraped_reviews(product_id: str, reviews: List[Dict[str, Any]]) -> int:
    """
    Wrapper for backward compatibility.
    """
    processed = await data_pipeline.process_reviews(reviews, product_id)
    return len(processed)
