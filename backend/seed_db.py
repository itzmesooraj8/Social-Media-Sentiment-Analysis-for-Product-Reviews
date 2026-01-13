
import asyncio
import os
import hashlib
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load env before importing database
load_dotenv()

from database import supabase, save_sentiment_analysis
from services.ai_service import ai_service

# Mock data - "Perfect" demo content
# Scenario: A mix of glowing reviews, some specific complaints (screen grain), and a bot attack.
REVIEWS = [
    {
        "text": "The S24 Ultra is an absolute beast! The titanium frame feels premium and the flat display is a game changer for S-Pen users. Battery life is easily 2 days. Best phone I've ever owned.",
        "platform": "reddit",
        "author": "TechEnthusiast99",
        "source_url": "https://reddit.com/r/Samsung/1",
        "timestamp_offset": 5 # minutes ago
    },
    {
        "text": "Finally switched from iPhone. The 5x zoom is actually more useful than the old 10x. AI features are a bit gimmicky but the 'Circle to Search' is genuinely useful. 9/10.",
        "platform": "twitter",
        "author": "@AndroidFan",
        "source_url": "https://twitter.com/AndroidFan/status/1",
        "timestamp_offset": 15
    },
    {
        "text": "WARNING: Display issues! getting weird graininess in low light. For a $1300 phone this is unacceptable. #S24Ultra #Fail",
        "platform": "twitter",
        "author": "@DisappointedUser",
        "source_url": "https://twitter.com/DisappointedUser/status/1",
        "timestamp_offset": 25
    },
    {
        "text": "Unboxing my Titanium Gray unit. The anti-reflective screen coating is magic. Validates the upgrade just for that alone.",
        "platform": "youtube",
        "author": "GadgetReviewer",
        "source_url": "https://youtube.com/watch?v=1",
        "timestamp_offset": 45
    },
    {
        "text": "Is anyone else facing overheating issues while gaming? Mine gets uncomfortably hot after 20 mins of Genshin.",
        "platform": "forums",
        "author": "GamerX",
        "source_url": "https://forums.samsung.com/1",
        "timestamp_offset": 60
    },
    # Bot Attack / Spam Cluster
    {
        "text": "CLICK HERE TO WIN FREE S24 ULTRA!!! BEST PRICE GUARANTEED BUY NOW CRYPTO BONUS",
        "platform": "twitter",
        "author": "@CryptoBot1",
        "source_url": "https://twitter.com/CryptoBot1/status/1",
        "timestamp_offset": 5
    },
    {
        "text": "WINNER WINNER S24 ULTRA GIVEAWAY CLICK LINK IN BIO",
        "platform": "twitter",
        "author": "@CryptoBot2",
        "source_url": "https://twitter.com/CryptoBot2/status/1",
        "timestamp_offset": 4
    }
]

async def seed_reviews():
    print("🌱 Starting Seed Script...")
    
    # 1. Get or Create Product (Samsung S24 Ultra)
    product_name = "Samsung Galaxy S24 Ultra"
    print(f"Checking product: {product_name}...")
    
    prod_res = supabase.table("products").select("id").eq("name", product_name).execute()
    if prod_res.data:
        product_id = prod_res.data[0]["id"]
        print(f"✓ Found existing product: {product_id}")
    else:
        # Create it
        new_prod = {
            "name": product_name,
            "description": "AI-powered flagship smartphone",
            "category": "Electronics",
            "keywords": ["s24", "ultra", "samsung", "camera", "ai"]
        }
        res = supabase.table("products").insert(new_prod).execute()
        product_id = res.data[0]["id"]
        print(f"✓ Created new product: {product_id}")

    # 2. Process Reviews
    success_count = 0
    
    for r in REVIEWS:
        try:
            # Create text hash
            text_hash = hashlib.md5(r["text"].encode('utf-8')).hexdigest()
            
            # Check if exists (dedupe)
            existing = supabase.table("reviews").select("id").eq("text_hash", text_hash).execute()
            if existing.data:
                print(f"Skipping duplicate: {r['text'][:30]}...")
                continue
                
            # Insert Review via Supabase
            # Note: We manually insert to ensure timestamps are recent
            created_at = (datetime.utcnow() - timedelta(minutes=r["timestamp_offset"])).isoformat()
            
            review_data = {
                "product_id": product_id,
                "text": r["text"],
                "platform": r["platform"],
                "source_url": r["source_url"],
                "author": r["author"],
                "text_hash": text_hash,
                "created_at": created_at
            }
            
            res = supabase.table("reviews").insert(review_data).execute()
            if not res.data:
                print("Failed to insert review")
                continue
                
            review_id = res.data[0]["id"]
            
            # analyze sentiment
            print(f"Analyzing: {r['text'][:30]}...")
            analysis = await ai_service.analyze_sentiment(r["text"])
            
            # Save Analysis
            analysis_data = {
                "review_id": review_id,
                "product_id": product_id,
                "label": analysis.get("label"),
                "score": analysis.get("score"),
                "emotions": analysis.get("emotions", []),
                "credibility": analysis.get("credibility", 0),
                "credibility_reasons": analysis.get("credibility_reasons", []),
                "aspects": analysis.get("aspects", [])
            }
            await save_sentiment_analysis(analysis_data)
            success_count += 1
            
        except Exception as e:
            print(f"Error processing review: {e}")

    print(f"✅ Seeding Complete! Added {success_count} new reviews.")

if __name__ == "__main__":
    asyncio.run(seed_reviews())
