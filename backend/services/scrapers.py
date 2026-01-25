import asyncio
import logging
from typing import List, Dict, Optional

# Import scrapers (assuming they are in the same package or available in path)
from services import youtube_scraper
from services import reddit_scraper
from services import twitter_scraper
from services import data_pipeline

logger = logging.getLogger(__name__)

async def scrape_all(product_keywords: List[str], product_id: str, url: Optional[str] = None) -> Dict[str, int]:
    """
    Orchestrator to run all available scrapers in parallel.
    Prioritizes YouTube and Reddit as stable sources.
    """
    logger.info(f"Starting scrape_all for {product_id} with keywords: {product_keywords}")
    
    tasks = []
    
    # 1. YouTube Scraper task
    tasks.append(youtube_scraper.scrape_youtube(product_keywords, limit=20))
    
    # 2. Reddit Scraper task
    tasks.append(reddit_scraper.scrape_reddit(product_keywords, limit=20))
    
    # 3. Twitter Scraper task (Optional/Volatility handling)
    tasks.append(twitter_scraper.scrape_twitter(product_keywords, limit=20))

    # Execute all scrapers in parallel
    results_list = await asyncio.gather(*tasks, return_exceptions=True)
    
    youtube_results = []
    reddit_results = []
    twitter_results = []
    
    # Unpack results safely
    # Result 0: YouTube
    if isinstance(results_list[0], list):
        youtube_results = results_list[0]
    else:
        logger.error(f"YouTube scraper failed: {results_list[0]}")
        
    # Result 1: Reddit
    if isinstance(results_list[1], list):
        reddit_results = results_list[1]
    else:
        logger.error(f"Reddit scraper failed: {results_list[1]}")

    # Result 2: Twitter
    if isinstance(results_list[2], list):
        twitter_results = results_list[2]
    else:
        logger.error(f"Twitter scraper failed: {results_list[2]}")
        
    # Combine all valid results
    all_raw_data = youtube_results + reddit_results + twitter_results
    
    logger.info(f"Scraping complete. Found {len(all_raw_data)} total items.")
    
    # Process and Save (Sent to Pipeline)
    # The pipeline handles AI processing, Sentiment Analysis, and DB insertion
    saved_count = 0
    if all_raw_data:
        saved_count = await data_pipeline.process_and_save(all_raw_data, product_id)
        
    return {
        "status": "completed",
        "total_scraped": len(all_raw_data),
        "total_saved": saved_count,
        "sources": {
            "youtube": len(youtube_results),
            "reddit": len(reddit_results),
            "twitter": len(twitter_results)
        }
    }