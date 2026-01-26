"""Twitter scraper service.

STRICT MODE: This service ONLY works if valid Twitter API keys are present.
It does NOT use Nitter (ntscraper) as it is unreliable.
It does NOT use mock data.
"""

import logging
import asyncio
import os
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

try:
    import tweepy
    _TWEEPY_AVAILABLE = True
except ImportError:
    _TWEEPY_AVAILABLE = False

class TwitterScraperService:
    def __init__(self) -> None:
        self.bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
        self.tweepy_client = None
        
        if _TWEEPY_AVAILABLE and self.bearer_token:
            try:
                self.tweepy_client = tweepy.Client(bearer_token=self.bearer_token)
                logger.info("Twitter: Authenticated with Tweepy (Official API)")
            except Exception as e:
                logger.error(f"Twitter: Tweepy auth failed: {e}")
        else:
            logger.warning("Twitter: Keys missing or Tweepy not installed. Scraping disabled.")

    async def search_tweets(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Public async API.
        Returns:
            List of tweets if keys exist and API works.
            Empty list [] if keys missing or error.
        """
        if not self.tweepy_client:
            logger.warning("Twitter API keys missing - skipping search.")
            return []

        try:
            return await asyncio.to_thread(self._run_tweepy, query, limit)
        except Exception as e:
            # We catch it here to log the specific query context
            logger.exception(f"Tweepy search failed for query '{query}'")
            return []

    def _run_tweepy(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Blocking Tweepy call."""
        results = []
        try:
            # Recent search (last 7 days)
            resp = self.tweepy_client.search_recent_tweets(
                query=query, 
                max_results=min(100, max(10, limit)),
                tweet_fields=['created_at', 'public_metrics', 'author_id']
            )
            
            if not resp.data:
                return []

            for t in resp.data:
                metrics = t.public_metrics or {}
                results.append({
                    'text': t.text,
                    'url': f"https://twitter.com/user/status/{t.id}",
                    'platform': 'twitter',
                    'posted_at': t.created_at.isoformat() if t.created_at else None,
                    'like_count': metrics.get('like_count', 0),
                    'retweet_count': metrics.get('retweet_count', 0),
                    'reply_count': metrics.get('reply_count', 0),
                    'username': str(t.author_id)
                })
            return results
        except Exception as e:
            # Re-raise to ensure it's caught/logged by the async wrapper
            raise e

twitter_scraper = TwitterScraperService()