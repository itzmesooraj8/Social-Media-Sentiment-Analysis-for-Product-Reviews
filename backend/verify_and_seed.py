import os
import sys
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

def main():
    print("🔍 VERIFYING DATABASE HEALTH...")
    
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        print("❌ CRITICAL: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env")
        sys.exit(1)

    supabase: Client = create_client(url, key)

    # 1. Test Product Creation (Checks for 'status' column)
    print("   Checking 'products' table schema...", end=" ")
    try:
        test_product = {
            "name": "Schema Test Product",
            "description": "Temporary test",
            "platform": "generic",
            "url": "http://test.com",
            "status": "active"  # This caused the error before
        }
        res = supabase.table("products").insert(test_product).execute()
        product_id = res.data[0]['id']
        print("✅ OK")
        
        # Clean up
        supabase.table("products").delete().eq("id", product_id).execute()
    except Exception as e:
        print(f"\n❌ FAILED. The 'products' table is missing columns.\n   Error: {str(e)}")
        print("\n⚠️  ACTION REQUIRED: You MUST run the SQL script in Supabase Dashboard!")
        sys.exit(1)

    # 1b. Test Reviews Table Schema (Crucial for Live Analyzer)
    print("   Checking 'reviews' table schema...", end=" ")
    try:
        # Try to select the specific columns that were causing crashes
        supabase.table("reviews").select("text, username, platform, source_url").limit(1).execute()
        print("✅ OK")
    except Exception as e:
        print(f"\n❌ FAILED. The 'reviews' table is outdated (Missing 'text' or 'username' columns).\n   Error: {str(e)}")
        print("\n⚠️  ACTION REQUIRED: Copy/Paste content of 'backend/schema_extra.sql' into Supabase SQL Editor!")
        sys.exit(1)

    # 2. Seed Live Data
    print("\n🌱 SEEDING DEMO DATA...")
    try:
        # Check if we already have the main product
        existing = supabase.table("products").select("id").eq("name", "Samsung Galaxy S24 Ultra").execute()
        
        if not existing.data:
            # Create Product
            prod_data = {
                "name": "Samsung Galaxy S24 Ultra",
                "description": "Latest flagship smartphone with AI features",
                "platform": "youtube",
                "url": "https://www.youtube.com/watch?v=sS_wWAoU0gI",
                "status": "active",
                "image_url": "https://images.samsung.com/is/image/samsung/p6pim/in/feature/164099842/in-feature-galaxy-s24-s928-539322308"
            }
            prod_res = supabase.table("products").insert(prod_data).execute()
            pid = prod_res.data[0]['id']
            print(f"   Created Product: Samsung Galaxy S24 Ultra")

            # Create Reviews
            reviews = [
                {"text": "The camera zoom is absolutely insane! Best phone of 2024.", "sentiment": "positive", "score": 0.95},
                {"text": "Battery life is better than my iPhone 15 Pro Max.", "sentiment": "positive", "score": 0.88},
                {"text": "Too expensive for what it offers. The AI features are gimmicky.", "sentiment": "negative", "score": -0.4},
                {"text": "It's okay, but the screen creates a weird glare.", "sentiment": "neutral", "score": 0.1},
                {"text": "S-Pen is useful but I rarely use it. Good build quality though.", "sentiment": "positive", "score": 0.6}
            ]
            
            review_payload = []
            for r in reviews:
                review_payload.append({
                    "product_id": pid,
                    "text": r["text"],
                    "content": r["text"], # Dual-write to satisfy schema
                    "username": f"User{random.randint(100,999)}",
                    "author": f"User{random.randint(100,999)}", # Dual-write
                    "source": "youtube",
                    "platform": "youtube", 
                    "sentiment_label": r["sentiment"],
                    "sentiment_score": r["score"],
                    "created_at": (datetime.now() - timedelta(hours=random.randint(1, 48))).isoformat()
                })
            
            supabase.table("reviews").insert(review_payload).execute()
            print(f"   Added {len(review_payload)} reviews.")
            
            # Create Alerts
            supabase.table("alerts").insert({
                "type": "negative_spike",
                "threshold": 0.7,
                "keywords": ["overheating", "bug"],
                "is_active": True
            }).execute()
            print("   Created default alerts.")
            
        else:
            print("   Data already exists. Skipping seed.")

    except Exception as e:
        print(f"❌ Seeding Error: {e}")

    print("\n✅ SYSTEM READY FOR CLIENT DEMO.")

if __name__ == "__main__":
    main()
