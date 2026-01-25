import asyncio
from services.youtube_scraper import youtube_scraper
from services.reddit_scraper import reddit_scraper
from services.twitter_scraper import twitter_scraper
from services.ai_service import ai_service
from services.data_pipeline import data_pipeline

async def scrape_all(product_keywords: list, product_id: str):
    """
    Orchestrator to run all scrapers in parallel for a given set of keywords,
    then process the results through the data pipeline.
    """
    print(f"[{product_id}] 🚀 Deploying scrapers for keywords: {product_keywords}")

    tasks = []
    # Launch all scrapers for all keywords in parallel
    for keyword in product_keywords:
        tasks.append(youtube_scraper.search_video_comments(keyword, max_results=20))
        tasks.append(reddit_scraper.search_product_mentions(keyword, limit=20))
        # Twitter is often fragile, so we wrap it to ensure it doesn't kill the batch
        tasks.append(twitter_scraper.search_tweets(keyword, limit=20))

    # await asyncio.gather runs them concurrently
    # return_exceptions=True prevents one failure from crashing the whole lot
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
            # Simple heuristic to count sources based on list content
            # Assuming scrapers return list of dicts with 'platform' key or similar
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