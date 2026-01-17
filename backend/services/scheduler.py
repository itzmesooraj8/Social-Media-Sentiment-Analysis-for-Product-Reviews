from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from services.reddit_scraper import reddit_scraper
from services.data_pipeline import process_scraped_reviews
from database import get_products
import asyncio
from datetime import datetime

scheduler = AsyncIOScheduler()

async def run_automated_scraping_job():
    """
    Background job to scrape REAL reviews for all active products.
    """
    print(f"[{datetime.now()}] 🔄 Starting automated scraping job (REAL DATA ONLY)...")
    
    try:
        products = await get_products()
        if not products:
            print("No active products found in database.")
            return

        total_new_reviews = 0
        
        for product in products:
            try:
                if not product.get('name'):
                    continue
                    
                print(f"  🔍 Scraping real-time data for: {product['name']}...")
                
                # 1. Scrape Reddit (Real API)
                # We limit to 20 per cycle to respect API rate limits while keeping data fresh
                reviews = await reddit_scraper.search_product_mentions(
                    product_name=product['name'],
                    subreddits=['all'], 
                    limit=20 
                )
                
                if reviews:
                    saved_count = await process_scraped_reviews(product['id'], reviews)
                    total_new_reviews += saved_count
                    print(f"    ✅ Saved {saved_count} new reviews from Reddit")
                else:
                    print(f"    ℹ️ No new content found on Reddit")

            except Exception as e:
                print(f"    ❌ Error scraping {product.get('name')}: {e}")
                continue
                
        print(f"[{datetime.now()}] ✅ Automation finished. Total new real reviews: {total_new_reviews}")
        
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Automated scraping job failed: {e}")

def start_scheduler():
    scheduler.add_job(
        run_automated_scraping_job,
        trigger=IntervalTrigger(minutes=30),
        id='scraping_job',
        name='Scrape Real Data',
        replace_existing=True
    )
    
    # Run immediately on startup
    scheduler.add_job(
        run_automated_scraping_job,
        trigger='date',
        run_date=datetime.now().astimezone(),
        id='startup_scraping',
        name='Startup Run'
    )
    
    scheduler.start()
    print("✓ Real-time background scheduler active (30 min interval)")
