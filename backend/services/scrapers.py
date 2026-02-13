import asyncio
import logging
from typing import List, Any

try:
    from services import youtube_scraper, reddit_scraper, twitter_scraper, data_pipeline
except ImportError:
    # Local dev or mixed environment fallback
    try:
        import youtube_scraper
        import reddit_scraper
        import twitter_scraper
        import data_pipeline
    except ImportError:
        pass

logger = logging.getLogger(__name__)

async def _safe_execute(coro, source_name: str) -> List[Any]:
    """
    Execute a scraper task safely.
    If it fails, log the exception and return an empty list.
    This prevents one failure from crashing the entire batch.
    """
    try:
        logger.info(f"Launching scraper: {source_name}")
        results = await coro
        if results:
            logger.info(f"{source_name} returned {len(results)} items.")
        else:
            logger.warning(f"{source_name} returned no data.")
        return results or []
    except Exception as e:
        logger.exception(f"CRITICAL: Scraper failed for {source_name}")
        return []

async def scrape_all(keywords: list, product_id: str, target_url: str = None):
    """
    Orchestrate all scrapers in parallel with strict fault tolerance.
    """
    logger.info(f"Starting scrape job for Product={product_id} | Keywords={keywords}")
    tasks = []
    
    # 1. Direct URL Handling (Smart Scraping)
    if target_url:
        if "youtube.com" in target_url or "youtu.be" in target_url:
            tasks.append(_safe_execute(
                youtube_scraper.youtube_scraper.scrape_video_comments(target_url), 
                "YouTube-Direct"
            ))
        elif "reddit.com" in target_url:
            tasks.append(_safe_execute(
                reddit_scraper.reddit_scraper.search_product_mentions(target_url), 
                "Reddit-Direct"
            ))
    
    # 2. General Keyword Search (Parallel)
    for keyword in keywords:
        # YouTube
        if hasattr(youtube_scraper, 'youtube_scraper'):
            tasks.append(_safe_execute(
                youtube_scraper.youtube_scraper.search_video_comments(keyword), 
                f"YouTube-{keyword}"
            ))
        
        # Reddit
        if hasattr(reddit_scraper, 'reddit_scraper'):
            tasks.append(_safe_execute(
                reddit_scraper.reddit_scraper.search_product_mentions(keyword), 
                f"Reddit-{keyword}"
            ))
            
        # Twitter
        if hasattr(twitter_scraper, 'twitter_scraper'):
            tasks.append(_safe_execute(
                twitter_scraper.twitter_scraper.search_tweets(keyword), 
                f"Twitter-{keyword}"
            ))

    # 3. Execute all agents simultaneously
    # We use gather, but exceptions are already caught in _safe_execute
    # Broadcast localized updates
    try:
        from services.status_manager import status_manager
        await status_manager.broadcast_status(product_id, "running", 10, "Agents deployed...")
    except ImportError:
        pass

    results_lists = await asyncio.gather(*tasks)
    
    try:
        from services.status_manager import status_manager
        await status_manager.broadcast_status(product_id, "running", 50, "Aggregating results...")
    except ImportError:
        pass

    # 4. Flatten Results
    flat_results = []
    for r_list in results_lists:
        if r_list and isinstance(r_list, list):
            flat_results.extend(r_list)

    logger.info(f"Scraping complete. Total items found: {len(flat_results)}")
    
    # 5. Send to AI Pipeline
    if flat_results:
        try:
            from services.status_manager import status_manager
            await status_manager.broadcast_status(product_id, "running", 70, f"Analyzing {len(flat_results)} reviews with AI...")
            
            logger.info("Sending data to AI pipeline...")
            await data_pipeline.process_reviews(flat_results, product_id)
            logger.info("AI pipeline processing started.")
            
            await status_manager.broadcast_status(product_id, "completed", 100, "Analysis complete.")
        except Exception as e:
            logger.exception("AI Pipeline failed")
            try:
                from services.status_manager import status_manager
                await status_manager.broadcast_status(product_id, "failed", 100, "AI Analysis failed.")
            except: pass
    else:
        try:
            from services.status_manager import status_manager
            await status_manager.broadcast_status(product_id, "completed", 100, "No new data found.")
        except: pass
    
    return {
        "status": "completed", 
        "count": len(flat_results),
        "product_id": product_id
    }
