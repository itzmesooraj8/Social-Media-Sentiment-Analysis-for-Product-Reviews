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

        client_id = os.environ.get("REDDIT_CLIENT_ID")
        client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
        user_agent = os.environ.get("REDDIT_USER_AGENT", "SentimentBeacon/1.0")

        if not client_id or not client_secret:
            print("Warning: Reddit credentials missing; Reddit scraping disabled.")
            return

        try:
            self.client = asyncpraw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)
        except Exception as e:
            print(f"Reddit client init failed: {e}")
            self.client = None

    async def search_product_mentions(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search Reddit (selected subreddits) for product mentions and return list of dicts.

        Each item: {"text": ..., "url": ..., "platform": "reddit", "posted_at": ISO timestamp}
        """
        if not self.client:
            return []

        subreddits = ["technology", "gadgets", "reviews"]
        per_sub = max(1, limit // len(subreddits))
        results: List[Dict[str, Any]] = []

        try:
            for sub in subreddits:
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
