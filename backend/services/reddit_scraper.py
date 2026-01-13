"""
Reddit scraping service for collecting product reviews
"""
import os
import asyncio
from typing import List, Dict, Any
from datetime import datetime

try:
    import praw
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False
    print("Warning: praw not installed. Install with: pip install praw")


class RedditScraperService:
    def __init__(self):
        self.reddit = None
        if PRAW_AVAILABLE:
            try:
                self.reddit = praw.Reddit(
                    client_id=os.environ.get("REDDIT_CLIENT_ID", ""),
                    client_secret=os.environ.get("REDDIT_CLIENT_SECRET", ""),
                    user_agent=os.environ.get("REDDIT_USER_AGENT", "SentimentBeacon/1.0")
                )
                print("✓ Reddit client initialized")
            except Exception as e:
                print(f"Reddit client initialization failed: {e}")
    
    async def search_product_mentions(self, product_name: str, subreddits: List[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search for product mentions across Reddit
        """
        if not self.reddit:
            print("Reddit client not available")
            return []
        
        if subreddits is None:
            subreddits = ['all']
        
        reviews = []
        
        try:
            for subreddit_name in subreddits:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Search for product mentions
                for submission in subreddit.search(product_name, limit=limit, time_filter='month'):
                    # Add submission
                    reviews.append({
                        'text': f"{submission.title}. {submission.selftext}",
                        'author': str(submission.author),
                        'platform': 'reddit',
                        'source_url': f"https://reddit.com{submission.permalink}",
                        'created_at': datetime.fromtimestamp(submission.created_utc).isoformat(),
                        'score': submission.score,
                        'subreddit': subreddit_name
                    })
                    
                    # Add top comments
                    submission.comments.replace_more(limit=0)
                    for comment in submission.comments.list()[:10]:  # Top 10 comments
                        if len(comment.body) > 20:  # Skip very short comments
                            reviews.append({
                                'text': comment.body,
                                'author': str(comment.author),
                                'platform': 'reddit',
                                'source_url': f"https://reddit.com{comment.permalink}",
                                'created_at': datetime.fromtimestamp(comment.created_utc).isoformat(),
                                'score': comment.score,
                                'subreddit': subreddit_name
                            })
            
            print(f"✓ Found {len(reviews)} Reddit mentions for '{product_name}'")
            return reviews
            
        except Exception as e:
            print(f"Error scraping Reddit: {e}")
            return []


# Global instance
reddit_scraper = RedditScraperService()
