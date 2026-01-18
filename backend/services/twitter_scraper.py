"""Minimal twitter_scraper placeholder using ntscraper (nitter/ntscraper).
Full Twitter/X scraping will be implemented in later phases.
"""

import os
from typing import List, Dict, Any

try:
    import ntscraper
    _NT_AVAILABLE = True
except Exception:
    _NT_AVAILABLE = False


class TwitterScraperService:
    def __init__(self):
        if not _NT_AVAILABLE:
            print("ntscraper not available; Twitter scraping disabled for now.")
            self.client = None
        else:
            # ntscraper usage depends on library; keep simple
            self.client = ntscraper

    async def search_tweets(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        try:
            # This is a placeholder; actual implementation may call client.search or similar
            tweets = []
            return tweets
        except Exception as e:
            print(f"Twitter scrape error: {e}")
            return []


twitter_scraper = TwitterScraperService()
import asyncio
from typing import List, Dict, Any

class TwitterScraperService:
    def __init__(self):
        self.enabled = True

    async def search_tweets(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Scrape REAL tweets only. No mocks allowed.
        """
        tweets = await self._try_real_scrape(query, limit)

        if not tweets:
            print(f"No real tweets found for '{query}'. Returning empty results (Mocking disabled).")
            return []
            
        return tweets

    async def _try_real_scrape(self, query: str, limit: int) -> List[Dict[str, Any]]:
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._run_ntscraper, query, limit)
        except Exception as e:
            print(f"Twitter Scrape Error: {e}")
            return []

    def _run_ntscraper(self, query: str, limit: int):
        try:
            from ntscraper import Nitter
            # Note: Nitter instances can be flaky. If this fails, consider using the official Twitter API
            # if the client provides keys. For now, this is the best 'free' real-time method.
            scraper = Nitter(log_level=1, skip_instance_check=False)
            results = scraper.get_tweets(query, mode='term', number=limit)

            cleaned = []
            for t in results.get('tweets', []):
                cleaned.append({
                    "text": t['text'],
                    "author": t['user']['username'],
                    "platform": "twitter",
                    "source_url": t['link'],
                    "created_at": t['date'],
                    "likes": t['stats']['likes'],
                    "retweets": t['stats']['retweets']
                })
            return cleaned
        except ImportError:
            print("'ntscraper' not installed. Run: pip install ntscraper")
            return []
        except Exception as e:
            print(f"Nitter scrape failed: {e}")
            return []

twitter_scraper = TwitterScraperService()
