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
    async def reload_config(self):
        """Hot reload credentials from environment."""
        self.bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
        self.tweepy_client = None
        
        if _TWEEPY_AVAILABLE and self.bearer_token:
            try:
                self.tweepy_client = tweepy.Client(bearer_token=self.bearer_token)
                logger.info("Twitter: Re-authenticated with Tweepy (Hot Reload)")
            except Exception as e:
                logger.error(f"Twitter: Tweepy re-auth failed: {e}")
        else:
             logger.warning("Twitter: Config reloaded but credentials still missing.")

    def __init__(self) -> None:
        self.bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
        self.tweepy_client = None
        
        if _TWEEPY_AVAILABLE and self.bearer_token:
            try:
                self.tweepy_client = tweepy.Client(bearer_token=self.bearer_token)
                logger.info("Twitter: Authenticated with Tweepy (Official API)")
            except Exception as e:
                logger.error(f"Twitter: Tweepy auth failed: {e}")
        elif not _TWEEPY_AVAILABLE:
            logger.warning("Twitter: Tweepy not installed. Twitter scraping disabled.")
        elif not self.bearer_token:
             logger.warning("Twitter: No Bearer Token found. Twitter scraping disabled.")

    async def search_tweets(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Public async API.
        Prioritizes Official API (Tweepy), falls back to Nitter (Scraper).
        """
        results = []
        
        # 1. Try Official API
        if self.tweepy_client:
            try:
                results = await asyncio.to_thread(self._run_tweepy, query, limit)
                if results: return results
            except Exception as e:
                logger.warning(f"Tweepy search failed, failing over to Nitter: {e}")
        
        # 2. Fallback to Nitter
        if _NITTER_AVAILABLE:
            try:
                logger.info(f"Attempting Nitter scrape for '{query}'...")
                results = await asyncio.to_thread(self._run_nitter, query, limit)
            except Exception as e:
                logger.error(f"Nitter search failed: {e}")
                
        return results

    def _run_tweepy(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Blocking Tweepy call."""
        results = []
        # Recent search (last 7 days)
        try:
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
            logger.error(f"Tweepy execution error: {e}")
            raise e

    def _run_nitter(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Blocking Nitter call."""
        results = []
        try:
            scraper = Nitter(log_level=1, skip_instance_check=False)
            # Nitter instances are flaky, maybe iterate? rely on lib defaults for now.
            start = scraper.get_tweets(query, mode='term', number=limit)
             
            if not start or not start.get('tweets'):
                return []

            for t in start['tweets']:
                # Nitter dict structure
                results.append({
                    'text': t.get('text', ''),
                    'url': t.get('link', ''),
                    'platform': 'twitter',
                    'posted_at': t.get('date'),
                    'like_count': t.get('stats', {}).get('likes', 0),
                    'retweet_count': t.get('stats', {}).get('retweets', 0),
                    'reply_count': t.get('stats', {}).get('comments', 0),
                    'username': t.get('user', {}).get('username', '')
                })
            return results
        except Exception as e:
            logger.error(f"Nitter execution error: {e}")
            return []

twitter_scraper = TwitterScraperService()
