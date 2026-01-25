import asyncio
from services.youtube_scraper import youtube_scraper
from services.reddit_scraper import reddit_scraper
from services.twitter_scraper import twitter_scraper
from services.ai_service import ai_service
from services.data_pipeline import data_pipeline

async def scrape_all(product_keywords: list, product_id: str, target_url: str = None):
    """
    Orchestrator to run all scrapers. 
    If target_url is provided, it prioritizes that specific source.
    """
    print(f"[{product_id}] 🚀 Deploying scrapers. Keywords: {product_keywords}, Target URL: {target_url}")

    tasks = []

    # 1. Smart Scraping: Direct URL Handling
    if target_url:
        if "youtube.com" in target_url or "youtu.be" in target_url:
            print(f"[{product_id}] 🎯 Targeted YouTube Scrape: {target_url}")
            tasks.append(youtube_scraper.scrape_video_comments(target_url, max_results=100))
        elif "reddit.com" in target_url:
             print(f"[{product_id}] 🎯 Targeted Reddit Scrape: {target_url}")
             # We assume reddit_scraper handles URLs in its search or we need a specific method.
             # Current reddit_scraper.search_product_mentions takes a query. 
             # Ideally we'd have a specific method, but for now we pass the URL as query 
             # and hope the scraper handles it (most PRAW wrappers do if implemented right, 
             # but here we might just search for the URL or rely on existing logic).
             # Let's assume search_product_mentions can handle it or we stick to general search.
             # For this task, we'll append it as a search task.
             tasks.append(reddit_scraper.search_product_mentions(target_url, limit=100))

    # 2. General Keyword Search (Always run to get broader context, unless we want ONLY the url)
    # The prompt says: "General Keyword Search (Always run this too...)"
    for keyword in product_keywords:
        tasks.append(youtube_scraper.search_video_comments(keyword, max_results=20))
        tasks.append(reddit_scraper.search_product_mentions(keyword, limit=20))
        tasks.append(twitter_scraper.search_tweets(keyword, limit=20))

    # await asyncio.gather runs them concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_reviews = []
    youtube_count = 0
    reddit_count = 0
    twitter_count = 0

    for res in results:
        if isinstance(res, Exception):
            print(f"⚠️ Scraper error: {res}")
            continue
        if res:
            if len(res) > 0:
                platform = res[0].get('platform', 'unknown')
                if platform == 'youtube': youtube_count += len(res)
                elif platform == 'reddit': reddit_count += len(res)
                elif platform == 'twitter': twitter_count += len(res)
            
            all_reviews.extend(res)

    print(f"[{product_id}] 📚 Found {len(all_reviews)} raw items from all sources.")

    if all_reviews:
        # Save to Supabase via data pipeline
        processed = await data_pipeline.process_reviews(all_reviews, product_id)
        print(f"[{product_id}] ✅ Saved {len(processed)} analyzed reviews.")
    else:
        print(f"[{product_id}] ⚠️ No reviews found.")

    return {
        "total": len(all_reviews),
        "youtube": youtube_count,
        "reddit": reddit_count,
        "twitter": twitter_count
    }