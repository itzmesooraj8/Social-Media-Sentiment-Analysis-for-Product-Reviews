
import asyncio
import os
from dotenv import load_dotenv

# Ensure backend directory is in python path
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

load_dotenv()

from database import supabase

async def main():
    print("Checking database...")
    if not supabase:
        print("Supabase client not initialized")
        return

    # Count products
    try:
        p_res = supabase.table("products").select("*", count="exact").execute()
        print(f"Products: {p_res.count}")
        if p_res.data:
            for p in p_res.data:
                print(f" - {p.get('name')} (ID: {p.get('id')})")
    except Exception as e:
        print(f"Error checking products: {e}")

    # Count reviews
    try:
        r_res = supabase.table("reviews").select("*", count="exact").execute()
        print(f"Reviews: {r_res.count}")
        if r_res.data and len(r_res.data) > 0:
            print(f"Sample review: {r_res.data[0].get('text')[:50]}...")
    except Exception as e:
        print(f"Error checking reviews: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
