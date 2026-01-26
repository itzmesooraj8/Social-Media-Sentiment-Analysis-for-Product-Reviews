
import asyncio
import os
import sys
# Ensure backend directory is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join("backend", ".env"))

print(f"API KEY PRESENT: {bool(os.environ.get('YOUTUBE_API_KEY'))}")

try:
    from backend.services.scrapers import scrape_all
except ImportError:
    # Fallback if running from root and package structure is tricky
    sys.path.append(os.path.join(os.getcwd(), "backend"))
    from services.scrapers import scrape_all

async def run_test():
    print("Starting test scrape for 'iPhone 15'...")
    try:
        # We need a valid product ID from the DB preferably, or a dummy one.
        # If we use a dummy one, it might fail FK constraints on inserting reviews if strict.
        # Let's fetch a product first.
        from backend.database import supabase
        prods = supabase.table("products").select("id").limit(1).execute()
        if not prods.data:
            print("No products in DB to attach reviews to. Creating dummy...")
            # Ideally we'd create one but let's assume one exists or use a random UUID if DB allows loose FK (unlikely)
            # We'll just try with a random UUID and see if it fails FK.
            import uuid
            pid = str(uuid.uuid4())
            # check if we can insert a product
            try:
                supabase.table("products").insert({"id": pid, "name": "Test Product"}).execute()
                print(f"Created temp product {pid}")
            except Exception as e:
                print(f"Could not create temp product: {e}. Trying to use existing.")
                if prods.data:
                   pid = prods.data[0]["id"]
                else:
                   print("Cannot proceed without product ID.")
                   return
            
        else:
            pid = prods.data[0]["id"]
            print(f"Using existing product ID: {pid}")

        result = await scrape_all(["iPhone 15"], pid)
        print("Scrape Result:", result)
        
    except Exception as e:
        print(f"Scrape Test Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_test())
