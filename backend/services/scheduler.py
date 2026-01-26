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
        
        # Scrape ALL active products
        for product in products:
            try:
                p_id = product.get("id")
                p_name = product.get("name")
                keywords = product.get("keywords") or [p_name]
                
                print(f"  > Processing product: {p_name} ({p_id})")
                
                # Call scrapers (Reddit disabled per request, but others active)
                # We pass None for 'url' to trigger auto-search mode in scrapers
                res = await scrapers.scrape_all(keywords, p_id, url=None)
                
                # Count stats
                if res and isinstance(res, dict):
                    total_new_reviews += res.get("saved", 0)
                    
            except Exception as pe:
                print(f"  ! Error processing product {product.get('name')}: {pe}")
                
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
