import asyncio
import sys
import os
from dotenv import load_dotenv

# Ensure backend directory is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Load env before imports that might need it
load_dotenv()

from services.url_processor import url_processor

async def main():
    test_url = "https://youtu.be/4KbrxIpQgkM?si=gIZqY7GjfpCB_yHG"
    print(f"🚀 Testing YouTube Analysis for: {test_url}")
    print("   Target Product: 'MKBHD S24 Review' (Test)")
    
    try:
        # Call the actual service logic used by the API
        result = await url_processor.process_url(test_url, product_name="MKBHD S24 Review")
        
        if result.get('status') == 'success':
            print("\n✅ Analysis Complete & Saved to DB!")
            print(f"   Product ID: {result.get('product_id')}")
            print(f"   Reviews Added: {result.get('reviews_added')}")
            print(f"   Platform: {result.get('platform')}")
        else:
            print(f"\n❌ Analysis Failed: {result.get('message')}")
            
    except Exception as e:
        print(f"\n❌ Script Error: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
