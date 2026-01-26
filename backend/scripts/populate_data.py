import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from database import add_product, get_products
from services import scrapers

async def populate():
    print("Starting Data Population...")
    
    # Define targets
    targets = [
        {"name": "iPhone 15", "keywords": ["iPhone 15", "iPhone 15 Pro", "apple battery life", "ios 17 bugs"]},
        {"name": "Tesla Model 3", "keywords": ["Tesla Model 3", "tesla quality", "tesla autopilot", "model 3 highland"]}
    ]
    
    existing = await get_products()
    existing_names = {p['name']: p['id'] for p in existing}
    
    for t in targets:
        pid = existing_names.get(t['name'])
        if not pid:
            print(f"Creating product: {t['name']}")
            res = await add_product({
                "name": t['name'],
                "keywords": t['keywords'],
                "track_twitter": True,
                "track_reddit": True,
                "track_youtube": True
            })
            # Handle list/dict return from add_product fallback/db
            if isinstance(res, list) and res:
                pid = res[0]['id']
            elif isinstance(res, dict):
                pid = res.get('id')
        else:
            print(f"Product exists: {t['name']} ({pid})")
            
        if pid:
            print(f"Triggering scrapers for {t['name']}...")
            # Youtube URL for comments (Optional specific target)
            target_url = None
            if "iPhone" in t['name']:
                 target_url = "https://www.youtube.com/watch?v=x98K5Zq2ejo" # MKBHD iPhone 15 Review
            elif "Tesla" in t['name']:
                 target_url = "https://www.youtube.com/watch?v=2vH8_g0_lXk" # Tesla Review
                 
            await scrapers.scrape_all(t['keywords'], pid, target_url=target_url)
            print(f"Completed scrape for {t['name']}")

    print("Data Population Complete.")

if __name__ == "__main__":
    asyncio.run(populate())
