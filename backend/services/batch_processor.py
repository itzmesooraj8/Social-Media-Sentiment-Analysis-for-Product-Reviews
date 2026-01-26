import asyncio
import uuid
import logging
import time
from typing import List, Dict, Any, Optional
from services.ai_service import ai_service

logger = logging.getLogger(__name__)

class BatchProcessor:
    def __init__(self):
        # In-memory job store (replace with Redis/DB for production)
        self._jobs: Dict[str, Dict[str, Any]] = {}

    def create_job(self, total_items: int) -> str:
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = {
            "id": job_id,
            "status": "pending",
            "progress": 0,
            "total": total_items,
            "processed": 0,
            "created_at": time.time(),
            "results": [],
            "errors": []
        }
        return job_id

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self._jobs.get(job_id)

    async def process_texts(self, texts: List[str], job_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Process a list of texts in parallel/batches.
        If job_id is provided, updates status.
        """
        if job_id and job_id not in self._jobs:
             job_id = self.create_job(len(texts))
        elif not job_id:
             # Create a temporary internal job if not provided
             job_id = self.create_job(len(texts))

        job = self._jobs[job_id]
        job["status"] = "processing"
        
        chunk_size = 50 # Adjust based on complexity
        results = []
        
        try:
            # Process in chunks
            for i in range(0, len(texts), chunk_size):
                chunk = texts[i:i+chunk_size]
                
                # Use AI Service batch (or gather individual calls)
                # ai_service.analyze_batch uses asyncio.gather internally currently
                chunk_results = await ai_service.analyze_batch(chunk)
                
                results.extend(chunk_results)
                
                # Update progress
                job["processed"] += len(chunk)
                job["progress"] = int((job["processed"] / job["total"]) * 100)
                
                # Yield control briefly
                await asyncio.sleep(0)

            job["status"] = "completed"
            job["results"] = results # Warning: keeping all results in memory
            job["completed_at"] = time.time()
            
        except Exception as e:
            logger.exception(f"Batch processing failed for job {job_id}")
            job["status"] = "failed"
            job["error"] = str(e)
            
        return results

    async def run_pipeline(self, raw_data: List[Dict[str, Any]], product_id: str) -> str:
        """
        Full pipeline: 
        1. Extract text from raw data
        2. Analyze
        3. Store in DB (Stub)
        """
        texts = [item.get("text") or item.get("content") or "" for item in raw_data]
        texts = [t for t in texts if t.strip()] # Filter empty
        
        job_id = self.create_job(len(texts))
        
        # Run in background
        asyncio.create_task(self._pipeline_task(texts, raw_data, product_id, job_id))
        
        return job_id

    async def _pipeline_task(self, texts: List[str], raw_data: List[Dict], product_id: str, job_id: str):
        try:
            analyzed_results = await self.process_texts(texts, job_id)
            
            # Here we would merge back with raw_data metadata and save to DB
            # For now, just mark done.
            # In a real app, we'd call database.save_reviews(...)
            
            # Extract topics for the whole batch
            topics = ai_service.extract_topics_lda(texts)
            self._jobs[job_id]["topics"] = topics
            
        except Exception as e:
            logger.error(f"Pipeline task failed: {e}")
            self._jobs[job_id]["status"] = "failed"
            self._jobs[job_id]["error"] = str(e)

batch_processor = BatchProcessor()
