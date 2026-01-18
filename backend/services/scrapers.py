"""Consolidated scrapers: YouTube (google-api-python-client), Reddit (asyncpraw), Twitter (ntscraper).

Each function returns a list of items with keys:
  { content, author, platform, source_url, created_at }

If a library or credentials are missing, the implementation degrades gracefully and returns [].
"""

import os
import re
import asyncio
from typing import List, Dict, Any

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    _YOUTUBE_AVAILABLE = True
except Exception:
    _YOUTUBE_AVAILABLE = False
    HttpError = Exception

try:
    import asyncpraw
    _REDDIT_AVAILABLE = True
except Exception:
    _REDDIT_AVAILABLE = False

try:
    import ntscraper
    _NT_AVAILABLE = True
except Exception:
    _NT_AVAILABLE = False


async def search_youtube_comments(query: str, max_results: int = 50) -> List[Dict[str, Any]]:
    if not _YOUTUBE_AVAILABLE:
        print("youtube client missing; skipping youtube scraping")
        return []

    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        print("YOUTUBE_API_KEY missing; skipping youtube scraping")
        return []

    def _sync(query, max_results):
        try:
            client = build("youtube", "v3", developerKey=api_key)
            # if query seems like url, extract id
            video_id = None
            if "youtube.com" in query or "youtu.be" in query:
                m = re.search(r"(?:v=|/)([0-9A-Za-z_-]{11})", query)
                if m:
                    video_id = m.group(1)
            if not video_id:
                resp = client.search().list(q=query, part="id", type="video", maxResults=1).execute()
                items = resp.get("items") or []
                if not items:
                    return []
                video_id = items[0]["id"]["videoId"]

            comments = []
            fetched = 0
            page_token = None
            while fetched < max_results:
                params = {"part": "snippet", "videoId": video_id, "maxResults": min(100, max_results - fetched), "textFormat": "plainText"}
                if page_token:
                    params["pageToken"] = page_token
                resp = client.commentThreads().list(**params).execute()
                for item in resp.get("items", []):
                    top = item["snippet"]["topLevelComment"]["snippet"]
                    comments.append({
                        "content": top.get("textDisplay"),
                        "author": top.get("authorDisplayName"),
                        "platform": "youtube",
                        "source_url": f"https://youtu.be/{video_id}",
                        "created_at": top.get("publishedAt"),
                    })
                    fetched += 1
                    if fetched >= max_results:
                        break
                page_token = resp.get("nextPageToken")
                if not page_token:
                    break
            return comments
        except HttpError as he:
            print(f"YouTube HttpError: {he}")
            return []
        except Exception as e:
            print(f"YouTube error: {e}")
            return []

    return await asyncio.to_thread(_sync, query, max_results)


async def search_reddit(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    if not _REDDIT_AVAILABLE:
        print("asyncpraw missing; skipping reddit scraping")
        return []

    cid = os.environ.get("REDDIT_CLIENT_ID")
    secret = os.environ.get("REDDIT_CLIENT_SECRET")
    ua = os.environ.get("REDDIT_USER_AGENT", "SentimentBeacon/1.0")
    if not cid or not secret:
        print("Reddit credentials missing; skipping reddit scraping")
        return []

    results = []
    try:
        reddit = asyncpraw.Reddit(client_id=cid, client_secret=secret, user_agent=ua)
        subreddit = reddit.subreddit("all")
        async for submission in subreddit.search(query, limit=limit):
            results.append({
                "content": submission.title + "\n" + (submission.selftext or ""),
                "author": str(submission.author) if submission.author else "",
                "platform": "reddit",
                "source_url": f"https://reddit.com{submission.permalink}",
                "created_at": submission.created_utc,
            })
        await reddit.close()
    except Exception as e:
        print(f"Reddit error: {e}")
    return results


async def search_twitter(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    if not _NT_AVAILABLE:
        print("ntscraper missing; skipping twitter scraping")
        return []

    try:
        # ntscraper provides blocking APIs; run in thread
        def _sync(q, limit):
            try:
                # Placeholder: actual usage depends on library api
                items = []
                return items
            except Exception as e:
                print(f"ntscraper error: {e}")
                return []

        return await asyncio.to_thread(_sync, query, limit)
    except Exception as e:
        print(f"Twitter search dispatch error: {e}")
        return []


async def run_all_scrapers(keywords: List[str], per_source: int = 50) -> List[Dict[str, Any]]:
    """Run YouTube/Reddit/Twitter scrapers in parallel for given keywords and return flattened results."""
    tasks = []
    for kw in keywords:
        tasks.append(search_youtube_comments(kw, max_results=per_source))
        tasks.append(search_reddit(kw, limit=min(20, per_source)))
        tasks.append(search_twitter(kw, limit=min(20, per_source)))

    gathered = await asyncio.gather(*tasks, return_exceptions=True)
    results = []
    for g in gathered:
        if isinstance(g, Exception):
            print(f"Scraper task error: {g}")
            continue
        results.extend(g or [])

    # Simple dedupe by content
    seen = set()
    out = []
    for it in results:
        c = (it.get("content") or "").strip()
        if not c or c in seen:
            continue
        seen.add(c)
        out.append(it)

    return out
