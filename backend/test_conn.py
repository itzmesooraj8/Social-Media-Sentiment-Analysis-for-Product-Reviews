
import asyncio
from database import supabase, get_products

async def test():
    print("Testing get_products connection...")
    try:
        if not supabase:
            print("Supabase client is NONE (using local DB fallback)")
        else:
            print("Supabase client is initialized. Attempting fetch...")
        
        products = await get_products()
        print(f"Successfully fetched {len(products)} products.")
        print(products)
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test())
