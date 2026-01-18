from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
# from services.reddit_scraper import reddit_scraper # Disabled per user request
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
        
        # Youtube Logic only now? The user said "Active Youtube" but scheduler usually runs passively.
        # Since youtube scraper needs a specific video URL or query usually, passive scraping is harder without a "keywords" list loop.
        # But we will disable Reddit here explicitly.
        
        print("ℹ️ Reddit scheduler disabled by user request. Automated scraping currently paused to save resources until YouTube auto-search is implemented.")
        
        # Future: Iterate products and search youtube? 
        # for product in products:
             # search_youtube(product.name) ...
                
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
    print("✓ Real-time background scheduler active (30 min interval) - REDDIT DISABLED")
