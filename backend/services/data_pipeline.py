import hashlib
import json
import re
from typing import List, Dict, Any
from datetime import datetime
from database import supabase, save_sentiment_analysis
from services.ai_service import ai_service

class DataPipelineService:
    def _clean_text(self, text: str) -> str:
        """
        Aggressively clean text: remove URLs, hashtags, special chars, emojis.
        """
        if not text:
            return ""
        
        # Remove URLs
        text = re.sub(r'http\S+', '', text)
        # Remove hashtags
        text = re.sub(r'#\w+', '', text)
        # Remove emojis/special chars (keep alphanumeric and basic punctuation)
        # This regex keeps letters, numbers, spaces, and .,!?'-
        text = re.sub(r'[^\w\s.,!?\'-]', '', text)
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    async def process_reviews(self, reviews: List[Dict[str, Any]], product_id: str) -> List[Dict[str, Any]]:
        """
        Cleaning, Sentiment Analysis (via AI Service), and Saving to DB.
        """
        if not reviews:
            return []

        processed_reviews = []
        saved_count = 0
        
        for review in reviews:
            raw_content = review.get("text") or review.get("content", "")
            if not raw_content:
                continue
            
            # Aggressive Cleaning
            content = self._clean_text(raw_content)
            if not content:
                continue
                
            # 1. Analyze Sentiment using AI Service
            try:
                analysis = await ai_service.analyze_sentiment(content)
            except Exception as e:
                print(f"AI Analysis failed for review: {e}")
                # Fallback to neutral
                analysis = {"label": "NEUTRAL", "score": 0.5, "emotions": [], "credibility": 0}

            text_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            # 2. Prepare Review Data
            # 2. Prepare Review Data
            # Map 'text' to 'content' if your DB schema uses 'content' instead of 'text'
            # Based on the error "null value in column content", the DB column is named 'content'.
            
            review_data = {
                "product_id": product_id,
                "content": content, # MAPPED FOR DB SCHEMA (was 'text')
                "username": review.get("author") or review.get("username", "Anonymous"),
                "platform": review.get("platform", "web_upload"),
                "source_url": review.get("source_url", ""),
                "text_hash": text_hash,
                "created_at": review.get("created_at") or datetime.now().isoformat()
            }
            
            # 3. Save to Database
            try:
                # Save review
                # We try to exclude fields if they cause errors (robustness)
                try:
                    res = supabase.table("reviews").insert(review_data).execute()
                except Exception as e:
                    # Retry without text_hash if schema issue
                    if "text_hash" in str(e):
                        del review_data["text_hash"]
                        res = supabase.table("reviews").insert(review_data).execute()
                    else:
                        raise e

                review_id = res.data[0]["id"] if res.data else None
                
                # Save analysis linked to review
                if review_id:
                    analysis_data = {
                        "review_id": review_id,
                        "product_id": product_id,
                        "label": analysis.get("label"),
                        "score": analysis.get("score"),
                        "emotions": analysis.get("emotions", []),
                        "credibility": analysis.get("credibility", 0),
                        "credibility_reasons": analysis.get("credibility_reasons", []),
                        "aspects": analysis.get("aspects", [])
                    }
                    await save_sentiment_analysis(analysis_data)
                    saved_count += 1
                    
                processed_reviews.append({**review_data, "analysis": analysis})
                
            except Exception as e:
                print(f"Failed to save review: {e}")

        # --- Topic Extraction Integration ---
        try:
            # Gather all text from this batch
            all_texts = [r.get("content") or r.get("text") or "" for r in processed_reviews]
            if all_texts:
                topics = await asyncio.to_thread(ai_service.extract_topics, all_texts)
                
                # Save topics to 'topic_analysis' table
                # We treat each bigram as a "topic" for now
                for t in topics:
                    topic_data = {
                        "topic_name": t["topic"], # Corrected key
                        "sentiment": 0, # Placeholder
                        "size": t["count"],       # Corrected key
                        "keywords": t["topic"].split(),
                        "created_at": datetime.now().isoformat()
                    }
                    try:
                         # Insert or ignore (if we had a unique constraint, but we don't, so just insert)
                         # Real app would upsert or aggregate.
                         supabase.table("topic_analysis").insert(topic_data).execute()
                    except Exception as e:
                        print(f"Failed to save topic {t['text']}: {e}")
                        
        except Exception as e:
             print(f"Topic Extraction failed: {e}")

        print(f"Data Pipeline: Successfully processed and saved {saved_count}/{len(reviews)} reviews.")
        return processed_reviews

data_pipeline = DataPipelineService()

async def process_scraped_reviews(product_id: str, reviews: List[Dict[str, Any]]) -> int:
    """
    Wrapper for backward compatibility.
    """
    processed = await data_pipeline.process_reviews(reviews, product_id)
    return len(processed)
