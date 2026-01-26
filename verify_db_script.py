
import asyncio
import os
from dotenv import load_dotenv
from supabase import create_client

# Load env from backend/.env
env_path = os.path.join(os.path.dirname(__file__), "backend", ".env")
load_dotenv(env_path)

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

print(f"URL: {url}")
print(f"Key: {key[:5]}..." if key else "Key: None")

if not url or not key:
    print("Missing credentials!")
    exit(1)

supabase = create_client(url, key)

async def check_db():
    print("\n--- Checking Products ---")
    try:
        res = supabase.table("products").select("*").execute()
        print(f"Products found: {len(res.data)}")
        for p in res.data[:3]:
            print(f" - {p['id']} ({p.get('name')})")
    except Exception as e:
        print(f"Error fetching products: {e}")

    print("\n--- Checking Reviews ---")
    try:
        res = supabase.table("reviews").select("id, product_id, content").limit(5).execute()
        print(f"Reviews found (limit 5): {len(res.data)}")
        for r in res.data:
            print(f" - Review for {r['product_id']}: {r['content'][:30]}...")
    except Exception as e:
        print(f"Error fetching reviews: {e}")

    print("\n--- Checking Sentiment Analysis ---")
    try:
        res = supabase.table("sentiment_analysis").select("*").limit(5).execute()
        print(f"Analyses found (limit 5): {len(res.data)}")
    except Exception as e:
        print(f"Error fetching analyses: {e}")

if __name__ == "__main__":
    asyncio.run(check_db())
