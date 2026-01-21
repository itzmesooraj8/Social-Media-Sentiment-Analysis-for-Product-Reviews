"""Twitter scraper using ntscraper (Nitter) as a scraping fallback.

This module performs a best-effort fetch via `ntscraper`. If the library is
not available, or if Nitter rate-limits us, the service returns an empty list
and logs a warning instead of raising so the rest of the system remains
functional.
"""

import logging
import asyncio
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

try:
    from ntscraper import Nitter  # type: ignore
    _NT_AVAILABLE = True
except Exception:
    _NT_AVAILABLE = False


class TwitterScraperService:
    def __init__(self) -> None:
        if not _NT_AVAILABLE:
            logger.warning("ntscraper not installed; Twitter scraping disabled.")
            self._enabled = False
        else:
            self._enabled = True

    async def search_tweets(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Public async API: returns list of tweet-like dicts or [] on failure."""
        if not self._enabled:
            return []

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._run_ntscraper, query, limit)
        except Exception as e:
            logger.exception("Twitter scrape dispatch error")
            return []

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
                tweets.append({
                    'text': t.get('text'),
                    'url': t.get('link') or t.get('url'),
                    'platform': 'twitter',
                    'posted_at': t.get('date') or t.get('time')
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
