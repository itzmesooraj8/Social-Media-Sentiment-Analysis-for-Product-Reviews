from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from services.reddit_scraper import reddit_scraper
from services.data_pipeline import process_scraped_reviews
from services import scrapers
from database import get_products
import asyncio
from datetime import datetime, timedelta

scheduler = AsyncIOScheduler()

async def run_automated_scraping_job():
    """
    Background job to scrape REAL reviews for all active products.
    """
    print(f"[{datetime.now()}] [START] Starting automated scraping job (REAL DATA ONLY)...")
    
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
                
                # Call scrapers (Reddit ACTIVE)
                # We pass None for 'target_url' to trigger auto-search mode in scrapers
                res = await scrapers.scrape_all(keywords, p_id, target_url=None)
                
                # Count stats
                if res and isinstance(res, dict):
                    total_new_reviews += res.get("saved", 0)
                    
            except Exception as pe:
                print(f"  ! Error processing product {product.get('name')}: {pe}")
                
        print(f"[{datetime.now()}] [DONE] Automation finished. Total new real reviews: {total_new_reviews}")
        
    except Exception as e:
        print(f"[{datetime.now()}] [ERROR] Automated scraping job failed: {e}")

def start_scheduler():
    scheduler.add_job(
        run_automated_scraping_job,
        trigger=IntervalTrigger(minutes=30),
        id='scraping_job',
        name='Scrape Real Data',
        replace_existing=True
    )
    
    # Run delayed on startup (2 minutes delay)
    scheduler.add_job(
        run_automated_scraping_job,
        trigger='date',
        run_date=datetime.now().astimezone() + timedelta(minutes=2),
        id='startup_scraping',
        name='Startup Run'
    )
    
    scheduler.start()
    print("Checked Real-time background scheduler active (30 min interval) - REDDIT ACTIVE")
