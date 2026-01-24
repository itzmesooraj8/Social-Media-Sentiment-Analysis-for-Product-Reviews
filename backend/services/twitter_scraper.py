"""Twitter scraper using ntscraper (Nitter) as a scraping fallback.

This module performs a best-effort fetch via `ntscraper`. If the library is
not available, or if Nitter rate-limits us, the service returns an empty list
and logs a warning instead of raising so the rest of the system remains
functional.
"""

import logging
import asyncio
import os
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Try importing dependencies
try:
    from ntscraper import Nitter  # type: ignore
    _NT_AVAILABLE = True
except Exception:
    _NT_AVAILABLE = False

try:
    import tweepy
    _TWEEPY_AVAILABLE = True
except ImportError:
    _TWEEPY_AVAILABLE = False


class TwitterScraperService:
    def __init__(self) -> None:
        self.api_key = os.environ.get("TWITTER_API_KEY")
        self.api_secret = os.environ.get("TWITTER_API_SECRET")
        self.access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
        self.access_secret = os.environ.get("TWITTER_ACCESS_SECRET")
        self.bearer_token = os.environ.get("TWITTER_BEARER_TOKEN")
        
        self.tweepy_client = None
        if _TWEEPY_AVAILABLE and self.bearer_token:
            try:
                self.tweepy_client = tweepy.Client(bearer_token=self.bearer_token)
                logger.info("Twitter: Authenticated with Tweepy (Official API)")
            except Exception as e:
                logger.error(f"Twitter: Tweepy auth failed: {e}")
        
        if not _NT_AVAILABLE and not self.tweepy_client:
            logger.warning("ntscraper not installed and no Twitter keys; Twitter scraping disabled.")
            self._enabled = False
        else:
            self._enabled = True

    async def search_tweets(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Public async API: returns list of tweet-like dicts or [] on failure."""
        if not self._enabled:
            return []

        # 1. Try Official API first
        if self.tweepy_client:
            try:
                # Run in thread since tweepy is sync (mostly)
                return await asyncio.to_thread(self._run_tweepy, query, limit)
            except Exception as e:
                logger.error(f"Tweepy search failed, falling back to Nitter: {e}")
                # Fallthrough to Nitter

        # 2. Fallback to Nitter
        if _NT_AVAILABLE:
            try:
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(None, self._run_ntscraper, query, limit)
            except Exception as e:
                logger.exception("Twitter scrape dispatch error")
                return []
        
        return []

    def _run_tweepy(self, query: str, limit: int) -> List[Dict[str, Any]]:
        results = []
        try:
            # Recent search (last 7 days)
            # tweets fields: created_at, public_metrics (likes, retweets, replies)
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
                    'url': f"https://twitter.com/user/status/{t.id}", # ID is reliable, user handle not strictly needed for URL to work often
                    'platform': 'twitter',
                    'posted_at': t.created_at.isoformat() if t.created_at else None,
                    'like_count': metrics.get('like_count', 0),
                    'retweet_count': metrics.get('retweet_count', 0),
                    'reply_count': metrics.get('reply_count', 0)
                })
            return results
        except Exception as e:
            logger.error(f"Tweepy execution error: {e}")
            raise e

    def _run_ntscraper(self, query: str, limit: int) -> List[Dict[str, Any]]:
        try:
            scraper = Nitter(log_level=0, skip_instance_check=False)
            data = scraper.get_tweets(query, mode='term', number=limit)

            # Some Nitter wrappers may return an error key or raise; handle both.
            if not data:
                logger.debug("ntscraper returned empty response for query: %s", query)
                return []

            # Detect simple rate-limit indicators in the payload
            if isinstance(data, dict) and data.get('error'):
                err = str(data.get('error'))
                if 'rate' in err.lower() or '429' in err:
                    logger.warning("Nitter rate-limited for query '%s' - returning empty list", query)
                    return []

            tweets = []
            for t in (data.get('tweets') or []):
                stats = t.get('stats', {})
                tweets.append({
                    'text': t.get('text'),
                    'url': t.get('link') or t.get('url'),
                    'platform': 'twitter',
                    'posted_at': t.get('date') or t.get('time'),
                    'like_count': stats.get('likes', 0),
                    'retweet_count': stats.get('retweets', 0),
                    'reply_count': stats.get('comments', 0)
                })
            return tweets
        except ImportError:
            logger.warning("ntscraper not installed. Install with: pip install ntscraper")
            return []
        except Exception as e:
            # Inspect exception message for rate-limit patterns
            msg = str(e).lower()
            if 'rate' in msg or '429' in msg:
                logger.warning("Nitter appears rate-limited: %s", e)
                return []
            logger.exception("Nitter scrape failed: %s", e)
            return []


twitter_scraper = TwitterScraperService()
