import asyncio
import logging
from services import youtube_scraper, reddit_scraper, twitter_scraper, data_pipeline

logger = logging.getLogger(__name__)

async def scrape_all(keywords: list, product_id: str, target_url: str = None):
    logger.info(f"Starting scrape for {product_id} with keywords: {keywords}")
    tasks = []
    
    # 1. Direct URL Handling (Smart Scraping)
    if target_url:
        if "youtube.com" in target_url or "youtu.be" in target_url:
            logger.info("Detected YouTube URL")
            tasks.append(youtube_scraper.scrape_video_comments(target_url))
        elif "reddit.com" in target_url:
            logger.info("Detected Reddit URL")
            # Using search_product_mentions as fallback for direct post scraping if specialized method missing
            tasks.append(reddit_scraper.search_product_mentions(target_url))
    
    # 2. General Keyword Search (Parallel)
    for keyword in keywords:
        # Note: Scrapers are async in this codebase, so we await them via gather, no to_thread needed for these specific methods
        if hasattr(youtube_scraper, 'search_video_comments'):
            tasks.append(youtube_scraper.search_video_comments(keyword))
        
        if hasattr(reddit_scraper, 'search_product_mentions'):
            tasks.append(reddit_scraper.search_product_mentions(keyword))
            
        if hasattr(twitter_scraper, 'search_tweets'):
            tasks.append(twitter_scraper.search_tweets(keyword))

    # 3. Execute all agents simultaneously
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 4. Flatten and Save
    flat_results = []
    for res in results:
        if isinstance(res, list):
            flat_results.extend(res)
        elif isinstance(res, Exception):
            logger.error(f"Scraper error: {res}")

    logger.info(f"Scraping complete. Found {len(flat_results)} items.")
    
    # 5. Send to AI Pipeline (Sentiment + Topic Modeling)
    if flat_results:
        # data_pipeline instance has process_reviews method
        await data_pipeline.process_reviews(flat_results, product_id)
    
    return {"status": "completed", "count": len(flat_results)}