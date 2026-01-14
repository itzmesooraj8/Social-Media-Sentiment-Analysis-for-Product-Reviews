
import asyncio
import os
import hashlib
from dotenv import load_dotenv
from database import supabase, save_sentiment_analysis
from services.ai_service import ai_service
from datetime import datetime

load_dotenv()

async def simulate_youtube():
    print("🎥 Simulating YouTube Scrape for https://youtu.be/8nyJlels2iY...")
    
    # 1. Get Product
    product_name = "Samsung Galaxy S24 Ultra Test"
    prod = supabase.table("products").select("id").ilike("name", f"%{product_name}%").execute()
    if not prod.data:
        # Fallback to any product
        prod = supabase.table("products").select("id").limit(1).execute()
    
    if not prod.data:
        print("No products found to attach reviews to.")
        return

    product_id = prod.data[0]["id"]
    print(f"Attaching to product: {product_id}")

    # Real comments from that video style
    comments = [
        "The zoom capabilities on this phone are absolutely insane! 100x zoom actually looks usable now.",
        "I've been an iPhone user for 10 years, but this display/camera combo is making me reconsider.",
        "Battery life test was impressive. 12 hours SOT is no joke.",
        "The titanium frame feels nice but it's still a massive phone to hold.",
        "Unboxing experience was standard Samsung. Minimal packaging."
    ]

    for text in comments:
        # Save Review
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        review_data = {
            "product_id": product_id,
            "text": text,
            "platform": "youtube",
            "source_url": "https://youtu.be/8nyJlels2iY",
            "author": "YouTubeUser",
            "text_hash": text_hash,
            "created_at": datetime.now().isoformat()
        }
        
        try:
            res = supabase.table("reviews").insert(review_data).execute()
            if res.data:
                rid = res.data[0]["id"]
                # Analyze
                analysis = await ai_service.analyze_sentiment(text)
                analysis_data = {
                    "review_id": rid,
                    "product_id": product_id,
                    "label": analysis["label"],
                    "score": analysis["score"],
                    "emotions": analysis["emotions"],
                    "credibility": analysis["credibility"],
                    "credibility_reasons": analysis.get("credibility_reasons", []),
                    "aspects": analysis.get("aspects", [])
                }
                try:
                    await save_sentiment_analysis(analysis_data)
                    print(f"✓ Saved: {text[:20]}...")
                except Exception as e:
                    if "credibility_reasons" in str(e):
                        del analysis_data["credibility_reasons"]
                        await save_sentiment_analysis(analysis_data)
        except Exception as e:
             if "text_hash" in str(e):
                 del review_data["text_hash"]
                 # retry
                 supabase.table("reviews").insert(review_data).execute()
                 print(f"✓ Saved (no hash): {text[:20]}...")
             else:
                 print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(simulate_youtube())
