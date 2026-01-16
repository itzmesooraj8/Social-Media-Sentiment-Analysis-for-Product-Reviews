
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from services.reddit_scraper import reddit_scraper
from services.data_pipeline import process_scraped_reviews
from database import get_products, supabase
import asyncio
from datetime import datetime

# Initialize Scheduler
scheduler = AsyncIOScheduler()

async def run_automated_scraping_job():
    """
    Background job to scrape reviews for all active products.
    """
    print(f"[{datetime.now()}] 🔄 Starting automated scraping job...")
    
    try:
        # Get all active products
        products = await get_products()
        if not products:
            print("No products found to scrape.")
            return

        total_new_reviews = 0
        
        for product in products:
            try:
                # Skip if no keywords or name (sanity check)
                if not product.get('name'):
                    continue
                    
                print(f"Scraping for product: {product['name']}...")
                
                # Search Reddit
                # We can search for product Name or specific keywords
                # For now, just searching product name
                # reviews = await reddit_scraper.search_product_mentions(
                #     product_name=product['name'],
                #     subreddits=['all'], 
                #     limit=20 # Lower limit for automated checks
                # )
                
                # if reviews:
                #     saved_count = await process_scraped_reviews(product['id'], reviews)
                #     total_new_reviews += saved_count
                #     print(f"  -> Saved {saved_count} new reviews for {product['name']}")
                # else:
                #     print(f"  -> No new reviews found for {product['name']}")
                    
            except Exception as e:
                print(f"Error scraping product {product.get('name')}: {e}")
                continue
                
        print(f"[{datetime.now()}] ✅ Automated scraping finished. Total new reviews: {total_new_reviews}")
        
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Automated scraping job failed: {e}")

def start_scheduler():
    """
    Start the background scheduler.
    """
    # Run every 30 minutes
    scheduler.add_job(
        run_automated_scraping_job,
        trigger=IntervalTrigger(minutes=30),
        id='scraping_job',
        name='Scrape Reddit for all products',
        replace_existing=True
    )
    
    # Also run once immediately on startup (after 10 seconds delay to let server start)
    scheduler.add_job(
        run_automated_scraping_job,
        trigger='date',
        run_date=datetime.now().astimezone(), # Run ASAP
        id='startup_scraping',
        name='Startup Scraping Run'
    )
    
    scheduler.start()
    print("✓ Background scheduler started (Interval: 30 mins)")
