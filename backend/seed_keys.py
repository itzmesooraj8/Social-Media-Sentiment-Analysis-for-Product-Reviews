import os
import asyncio
from database import supabase


async def seed_keys():
    # User provided keys - Replace with your actual keys from environment variables or secure config
    youtube_key = os.environ.get("YOUTUBE_API_KEY", "")
    hf_token = os.environ.get("HF_TOKEN", "")
    
    # 1. Clear existing keys for clean slate
    print("Clearing existing integrations...")
    try:
        supabase.table("integrations").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    except Exception:
        pass # Might be empty or RLS

    # 2. Insert new keys
    integrations = [
        {
            "platform": "youtube",
            "api_key": youtube_key,
            "active": True
        },
        {
            "platform": "huggingface",
            "api_key": hf_token,
            "active": True
        }
    ]
    
    print("Inserting new keys...")
    try:
        res = supabase.table("integrations").insert(integrations).execute()
        print(f"Inserted {len(res.data)} keys successfully.")
    except Exception as e:
        print(f"Error inserting keys: {e}")

if __name__ == "__main__":
    asyncio.run(seed_keys())
