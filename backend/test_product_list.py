
import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure backend directory is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

load_dotenv()

from database import get_products, supabase

async def test_list_and_count():
    print("Testing Product List Logic...")
    try:
        products = await get_products()
        print(f"Found {len(products)} products.")
        
        for p in products:
            pid = p.get('id')
            pname = p.get('name')
            
            try:
                # Same logic as in main.py
                count_res = supabase.table("reviews").select("id", count="exact").eq("product_id", pid).execute()
                count = count_res.count or 0
                print(f"Product: {pname} | ID: {pid} | Count: {count}")
            except Exception as e:
                print(f"Error counting for {pname}: {e}")
                
    except Exception as e:
        print(f"Top level error: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_list_and_count())
