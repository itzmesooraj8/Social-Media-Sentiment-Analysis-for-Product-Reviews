
import random
import datetime
from typing import List, Dict, Any

# Mock Data Generator for "Demo Mode" or Falback

def _generate_mock_reviews(count: int, platform: str, keywords: List[str]) -> List[Dict[str, Any]]:
    reviews = []
    sentiments = ["Positive", "Negative", "Neutral", "Mixed"]
    
    positive_phrases = ["Love this product!", "Amazing quality", "Highly recommended", "Best purchase ever", "Great value"]
    negative_phrases = ["Terrible experience", "Waste of money", "Broken on arrival", "Customer service is bad", "Not worth it"]
    neutral_phrases = ["It's okay", "Average", "Decent but could be better", "Nothing special", "As expected"]
    
    keyword = keywords[0] if keywords else "product"

    for i in range(count):
        sentiment = random.choice(sentiments)
        if sentiment == "Positive":
            text = f"{random.choice(positive_phrases)}. {keyword} is great."
        elif sentiment == "Negative":
            text = f"{random.choice(negative_phrases)}. {keyword} disappointed me."
        else:
            text = f"{random.choice(neutral_phrases)}. {keyword} is just fine."

        reviews.append({
            "id": f"mock_{platform}_{i}",
            "text": text,
            "content": text, # normalize
            "platform": platform,
            "author": f"user_{random.randint(1000, 9999)}",
            "timestamp": datetime.datetime.now().isoformat(),
            "created_at": datetime.datetime.now().isoformat(),
            "url": f"https://{platform}.com/mock/{i}",
            "source_url": f"https://{platform}.com/mock/{i}",
            "likes": random.randint(0, 500),
            "like_count": random.randint(0, 500),
            "replies": random.randint(0, 50),
            "reply_count": random.randint(0, 50),
            "retweets": random.randint(0, 100),
            "retweet_count": random.randint(0, 100),
            "is_mock": True
        })
    return reviews

async def mock_search_youtube(keywords: List[str], limit=10):
    return _generate_mock_reviews(limit, "youtube", keywords)

async def mock_search_reddit(keywords: List[str], limit=10):
    return _generate_mock_reviews(limit, "reddit", keywords)

async def mock_search_twitter(keywords: List[str], limit=10):
    return _generate_mock_reviews(limit, "twitter", keywords)
