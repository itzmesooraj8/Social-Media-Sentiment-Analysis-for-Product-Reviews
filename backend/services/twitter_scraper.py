"""Twitter scraper using ntscraper (Nitter) as a scraping fallback.

If `ntscraper` is not available or an error occurs, the module logs a clear
message and returns an empty list.
"""

import os
import asyncio
from typing import List, Dict, Any

try:
    from ntscraper import Nitter
    _NT_AVAILABLE = True
except Exception:
    _NT_AVAILABLE = False


class TwitterScraperService:
    def __init__(self):
        if not _NT_AVAILABLE:
            print("Warning: ntscraper not installed; Twitter scraping disabled.")
            self._enabled = False
        else:
            self._enabled = True

    async def search_tweets(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search tweets using Nitter via `ntscraper`.

        Returns list of {text, url, platform, posted_at}.
        """
        if not self._enabled:
            return []

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._run_ntscraper, query, limit)
        except Exception as e:
            print(f"Twitter scrape dispatch error: {e}")
            return []

    def _run_ntscraper(self, query: str, limit: int) -> List[Dict[str, Any]]:
        try:
            scraper = Nitter(log_level=0, skip_instance_check=False)
            data = scraper.get_tweets(query, mode='term', number=limit)
            tweets = []
            for t in data.get('tweets', []):
                tweets.append({
                    'text': t.get('text'),
                    'url': t.get('link'),
                    'platform': 'twitter',
                    'posted_at': t.get('date')
                })
            return tweets
        except ImportError:
            print("ntscraper not installed. Install with: pip install ntscraper")
            return []
        except Exception as e:
            print(f"Nitter scrape failed: {e}")
            return []


twitter_scraper = TwitterScraperService()
