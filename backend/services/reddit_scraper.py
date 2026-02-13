"""Reddit scraper using asyncpraw.

Searches a small set of relevant subreddits and returns recent comments/posts
matching `query`.
"""

import os
import asyncio
from typing import List, Dict, Any
from datetime import datetime

try:
    import asyncpraw
    _PRAW_AVAILABLE = True
except Exception:
    _PRAW_AVAILABLE = False


class RedditScraperService:
    def __init__(self):
        self.client = None
        if not _PRAW_AVAILABLE:
            print("Warning: asyncpraw not installed; Reddit scraping disabled.")
            return

        # Attempt to see if credentials exist. If not, we just log and return.
        client_id = os.environ.get("REDDIT_CLIENT_ID", "")
        client_secret = os.environ.get("REDDIT_CLIENT_SECRET", "")
        # Allow running without keys (return empty results) instead of crashing or warning later? 
        # Actually user wants 'Real Time' so we must warn him to add keys.

        client_id = os.environ.get("REDDIT_CLIENT_ID")
        client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
        user_agent = os.environ.get("REDDIT_USER_AGENT", "SentimentBeacon/1.0")

        if not client_id or not client_secret:
            print("Warning: Reddit credentials missing; Reddit scraping disabled.")
            return

        try:
            # Proxy Configuration for High Reliability
            proxy_url = os.environ.get("REDDIT_PROXY")
            requestor_kwargs = {"proxy": proxy_url} if proxy_url else None
            
            self.client = asyncpraw.Reddit(
                client_id=client_id, 
                client_secret=client_secret, 
                user_agent=user_agent,
                requestor_kwargs=requestor_kwargs
            )
        except Exception as e:
            print(f"Reddit client init failed: {e}")
            self.client = None

    async def search_product_mentions(self, query: str, limit: int = 50, subreddits: List[str] = None) -> List[Dict[str, Any]]:
        """Search Reddit (dynamic subreddits or global) for product mentions.

        Each item: {"text": ..., "url": ..., "platform": "reddit", "posted_at": ISO timestamp}
        """
        if not self.client:
            return []

        targets = subreddits if subreddits else ["all"]
        per_sub = max(1, limit // len(targets))
        results: List[Dict[str, Any]] = []

        try:
            for sub in targets:
                try:
                    subreddit = await self.client.subreddit(sub)
                except Exception:
                    # fallback to name-based access
                    subreddit = self.client.subreddit(sub)

                # Search recent posts
                async for submission in subreddit.search(query, limit=per_sub, time_filter="month"):
                    # Add submission as a mention
                    posted = None
                    try:
                        posted = datetime.fromtimestamp(submission.created_utc).isoformat()
                    except Exception:
                        posted = None

                    results.append({
                        "text": (submission.title or "") + "\n" + (submission.selftext or ""),
                        "url": f"https://reddit.com{submission.permalink}",
                        "platform": "reddit",
                        "posted_at": posted,
                        "like_count": submission.score,
                        "reply_count": submission.num_comments
                    })

                    # Try to gather a few top-level comments
                    try:
                        await submission.comments.replace_more(limit=0)
                        # `submission.comments.list()` may be large; take first few
                        for comment in submission.comments.list()[:3]:
                            try:
                                posted_c = datetime.fromtimestamp(comment.created_utc).isoformat()
                            except Exception:
                                posted_c = None
                            results.append({
                                "text": comment.body,
                                "url": f"https://reddit.com{comment.permalink}",
                                "platform": "reddit",
                                "posted_at": posted_c,
                                "like_count": comment.score,
                                "reply_count": 0 # Comments might have replies but simple scraper won't traverse deep
                            })
                    except Exception:
                        # Comments retrieval failed for this submission
                        continue

                    if len(results) >= limit:
                        break

                if len(results) >= limit:
                    break

            # Trim to requested limit
            return results[:limit]

        except Exception as e:
            print(f"Reddit scraping error: {e}")
            return []


reddit_scraper = RedditScraperService()
