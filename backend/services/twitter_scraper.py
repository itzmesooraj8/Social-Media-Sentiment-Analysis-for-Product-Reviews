"""Twitter scraper service.

Uses Tweepy (Official API) if keys are present.
Falls back to Nitter (ntscraper) for no-auth scraping if keys are missing.
"""

import logging
import asyncio
import os
import random
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

try:
    import tweepy
    _TWEEPY_AVAILABLE = True
except ImportError:
    _TWEEPY_AVAILABLE = False

try:
    from ntscraper import Nitter
    _NITTER_AVAILABLE = True
except ImportError:
    _NITTER_AVAILABLE = False

class TwitterScraperService:
    def __init__(self) -> None:
        self.bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
        self.tweepy_client = None
        self.nitter_client = None
        
        if _TWEEPY_AVAILABLE and self.bearer_token:
            try:
                self.tweepy_client = tweepy.Client(bearer_token=self.bearer_token)
                logger.info("Twitter: Authenticated with Tweepy (Official API)")
            except Exception as e:
                logger.error(f"Twitter: Tweepy auth failed: {e}")
        
        # Nitter is lazy loaded to prevent startup hangs caused by 'aiohttp' session issues
        self.nitter_client = None 

    def _get_nitter(self):
        if not _NITTER_AVAILABLE: return None
        if not self.nitter_client:
            try:
                self.nitter_client = Nitter(log_level=1, skip_instance_check=False)
                logger.info("Twitter: Nitter scraper initialized (Lazy)")
            except Exception as e:
                logger.error(f"Twitter: Nitter init failed: {e}")
        return self.nitter_client

    async def search_tweets(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Public async API.
        """
        # 1. Try Official API
        if self.tweepy_client:
            try:
                return await asyncio.to_thread(self._run_tweepy, query, limit)
            except Exception as e:
                logger.warning(f"Tweepy search failed, falling back to Nitter: {e}")

        # 2. Try Nitter (No-Auth)
        if self._get_nitter():
            try:
                return await asyncio.to_thread(self._run_nitter, query, limit)
            except Exception as e:
                logger.error(f"Nitter search failed: {e}")
        
        return []

    def _run_tweepy(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Blocking Tweepy call."""
        results = []
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

    def _run_nitter(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Blocking Nitter call."""
        results = []
        nitter = self._get_nitter()
        if not nitter:
            return []

        # Nitter scraping
        # mode='term' searches for the query
        # number is approx
        scraped = nitter.get_tweets(query, mode='term', number=limit)
        
        tweets = scraped.get('tweets', [])
        for t in tweets:
            stats = t.get('stats', {})
            results.append({
                'text': t.get('text'),
                'url': t.get('link'),
                'platform': 'twitter',
                'posted_at': t.get('date'),
                'like_count': stats.get('likes', 0),
                'retweet_count': stats.get('retweets', 0),
                'reply_count': stats.get('comments', 0),
                'username': t.get('user', {}).get('username')
            })
            if len(results) >= limit:
                break
        
        return results

twitter_scraper = TwitterScraperService()
