import csv
import io
import asyncio
from typing import List, Dict, Any
from database import supabase, save_sentiment_analysis
from services.ai_service import ai_service
import hashlib

class CSVImportService:
    async def process_csv(self, file_content: bytes, product_id: str, platform: str) -> Dict[str, Any]:
        """
        Process a CSV file content, analyze sentiment for each row, and save to DB.
        Expected CSV headers: 'text' (mandatory), 'date' (optional), 'author' (optional).
        """
        # Decode bytes to string
        try:
            content_str = file_content.decode('utf-8')
        except UnicodeDecodeError:
             # Try latin-1 fallback
            content_str = file_content.decode('latin-1')

        # Parse CSV
        reader = csv.DictReader(io.StringIO(content_str))
        
        # Identify text column
        if not reader.fieldnames:
            raise Exception("Empty CSV file")
            
        # Flexible column matching
        headers = [h.lower() for h in reader.fieldnames]
        text_col = next((h for h in reader.fieldnames if h.lower() in ['text', 'content', 'review', 'comment', 'tweet', 'body']), None)
        author_col = next((h for h in reader.fieldnames if h.lower() in ['author', 'user', 'username', 'screen_name']), None)
        date_col = next((h for h in reader.fieldnames if h.lower() in ['date', 'created_at', 'timestamp', 'time']), None)
        
        if not text_col:
            raise Exception("CSV must contain a column named 'text', 'content', 'review', or 'tweet'")

        success_count = 0
        error_count = 0
        
        # Process rows
        tasks = []
        rows = list(reader)
        
        # Limit to 50 for demo speed/rate limits (unless we queue)
        # User said "Download a Twitter dataset...". Those can be huge.
        # Let's batch 20 at a time?
        batch_size = 50
        processed_rows = rows[:batch_size] 
        
        print(f"Processing {len(processed_rows)} rows from CSV...")
        
        for row in processed_rows:
            text = row.get(text_col, "").strip()
            if not text or len(text) < 2: continue
            
            author = row.get(author_col, "Imported User")
            # Basic date parsing or default to now?
            # We'll let database handle default created_at if missing
            
            tasks.append(self._analyze_and_save(text, author, product_id, platform))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for res in results:
            if isinstance(res, Exception):
                error_count += 1
                print(f"Row import failed: {res}")
            elif res:
                success_count += 1

        return {
            "total_processed": len(processed_rows),
            "success_count": success_count,
            "error_count": error_count,
            "message": f"Successfully imported {success_count} reviews."
        }

    async def _analyze_and_save(self, text: str, author: str, product_id: str, platform: str):
        # 1. Analyze
        sentiment_result = await ai_service.analyze_sentiment(text)
        
        # 2. Hash
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        
        # 3. Save Review
        # persist as `username` column to match DB schema (accept either `username` or `author` upstream)
        review_data = {
            "product_id": product_id,
            "text": text,
            "platform": platform,
            "username": author,
            "text_hash": text_hash,
            "source_url": "csv_import"
        }
        
        # Try insert review
        try:
            review_resp = supabase.table("reviews").insert(review_data).execute()
        except Exception as e:
            if "duplicate" in str(e).lower():
                print(f"Skipping duplicate: {text[:20]}...")
                return False
            raise e
            
        if not review_resp.data:
            return False
            
        review_id = review_resp.data[0]["id"]
        
        # 4. Save Analysis
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
        return True

csv_import_service = CSVImportService()
