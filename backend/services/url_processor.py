import asyncio
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

from services.youtube_scraper import youtube_scraper
from services.ai_service import ai_service


async def process_url(url: str, product_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Lightweight URL analysis that scrapes YouTube (and can be extended for Reddit),
    runs sentiment analysis on the first N comments and returns a short summary.

    This implementation is intentionally defensive for demo environments where
    API keys may be missing.
    """
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    platform = "unknown"
    reviews: List[Dict[str, Any]] = []

    try:
        if "youtube" in hostname or "youtu.be" in hostname:
            platform = "youtube"
            # youtube_scraper.search_video_comments accepts either a url or id
            reviews = youtube_scraper.search_video_comments(url, max_results=100)

        elif "reddit" in hostname or "redd.it" in hostname:
            platform = "reddit"
            # If reddit scraper is available, attempt to call it. Keep defensive.
            try:
                from services.reddit_scraper import reddit_scraper
                if hasattr(reddit_scraper, "search_product_mentions"):
                    # product_name is used as search when available
                    pname = product_name or parsed.path.strip('/') or "all"
                    reviews = await reddit_scraper.search_product_mentions(pname, limit=100)
            except Exception:
                reviews = []
        else:
            return {"status": "error", "message": "Unsupported URL platform. Only YouTube and Reddit are supported."}

        if not reviews:
            return {"status": "ok", "platform": platform, "count": 0, "reviews": []}

        # Run sentiment analysis concurrently (bounded)
        limit = 50
        to_analyze = reviews[:limit]

        async def _analyze_item(item: Dict[str, Any]):
            text = item.get("text") or item.get("content") or str(item)
            try:
                res = await ai_service.analyze_sentiment(text)
            except Exception:
                res = {"label": "NEUTRAL", "score": 0.5}
            return {"text": text, "analysis": res, "platform": item.get("platform", platform), "author": item.get("author") or item.get("username")}

        tasks = [asyncio.create_task(_analyze_item(i)) for i in to_analyze]
        analyzed = await asyncio.gather(*tasks, return_exceptions=True)

        # Normalize results
        results: List[Dict[str, Any]] = []
        for a in analyzed:
            if isinstance(a, Exception):
                continue
            results.append(a)

        # Summary counts
        pos = sum(1 for r in results if r.get("analysis", {}).get("label", "").upper() == "POSITIVE")
        neg = sum(1 for r in results if r.get("analysis", {}).get("label", "").upper() == "NEGATIVE")
        neut = len(results) - pos - neg

        return {
            "status": "success",
            "platform": platform,
            "count": len(results),
            "positive": pos,
            "neutral": neut,
            "negative": neg,
            "sample": results[:5]
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# Backwards-compatible sync wrapper for any callers expecting a sync function
def process_url_sync(url: str, product_name: Optional[str] = None) -> Dict[str, Any]:
    return asyncio.get_event_loop().run_until_complete(process_url(url, product_name))


__all__ = ["process_url", "process_url_sync"]
import asyncio
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

from services.youtube_scraper import youtube_scraper
from services.reddit_scraper import reddit_scraper
from services.ai_service import ai_service


async def _analyze_reviews_async(reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run `ai_service.analyze_sentiment` on reviews concurrently where possible."""
    results = []
    tasks = []
    for r in reviews:
        text = r.get("text", "")
        tasks.append(ai_service.analyze_sentiment(text))

    try:
        analyses = await asyncio.gather(*tasks, return_exceptions=True)
    except Exception:
        analyses = []

    for r, a in zip(reviews, analyses):
        if isinstance(a, Exception):
            # If analysis failed, attach minimal placeholder
            r["analysis"] = {"label": "NEUTRAL", "score": 0.5}
        else:
            r["analysis"] = a
        results.append(r)

    return results


def process_url(url: str, product_name: Optional[str] = None) -> Dict[str, Any]:
    """Detect platform from URL and run scraping + lightweight analysis.

    This function returns a summary and does NOT persist to DB unless the caller
    chooses to forward the reviews to the pipeline explicitly.
    """
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()

    platform = None
    reviews: List[Dict[str, Any]] = []

    # Detect platform
    if "youtube" in hostname or "youtu.be" in hostname:
        platform = "youtube"
        try:
            # youtube_scraper.search_video_comments may raise if API key missing
            reviews = youtube_scraper.search_video_comments(url, max_results=50)
        except Exception as e:
            return {"status": "error", "message": f"YouTube scrape failed: {e}"}

    elif "reddit" in hostname or "redd.it" in hostname:
        platform = "reddit"
        # reddit scraper is async for search; we call sync search if available
        try:
            # If reddit_scraper exposes async search_product_mentions, use it
            import asyncio as _asyncio
            if hasattr(reddit_scraper, "search_product_mentions"):
                # search_product_mentions expects product name; try to extract id from path or use product_name
                pname = product_name or parsed.path.strip('/') or "all"
                reviews = _asyncio.get_event_loop().run_until_complete(reddit_scraper.search_product_mentions(pname, limit=50))
        except Exception as e:
            return {"status": "error", "message": f"Reddit scrape failed: {e}"}
    else:
        return {"status": "error", "message": "Unsupported URL platform. Only YouTube and Reddit URLs are supported."}

    # If no reviews found
    if not reviews:
        return {"status": "ok", "platform": platform, "count": 0, "reviews": []}

    # Attempt to run analysis asynchronously (may fail if AI service not configured)
    try:
        analyzed = asyncio.get_event_loop().run_until_complete(_analyze_reviews_async(reviews))
    except Exception:
        # Fallback: attach no analysis
        analyzed = reviews

    # Build a lightweight summary
    pos = 0
    neg = 0
    neut = 0
    for r in analyzed:
        lab = None
        if isinstance(r.get("analysis"), dict):
            lab = r["analysis"].get("label")
        if lab:
            if lab.upper() == "POSITIVE": pos += 1
            elif lab.upper() == "NEGATIVE": neg += 1
            else: neut += 1
        else:
            neut += 1

    summary = {
        "status": "ok",
        "platform": platform,
        "count": len(analyzed),
        "positive": pos,
        "neutral": neut,
        "negative": neg,
        "sample": analyzed[:5]
    }

    return summary
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, parse_qs

from services.youtube_scraper import youtube_scraper
from services.reddit_scraper import reddit_scraper
from database import get_products, add_product


class UrlProcessorService:
    async def process_url(self, url: str, product_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Detect platform from URL, scrape content, run pipeline and save to DB.
        Returns summary dict.
        """
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()

        # Determine product id: if product_name provided, create/find product
        product_id = None
        if product_name:
            # Try to find existing product by name
            prods = await get_products()
            match = next((p for p in prods if p.get("name") and p.get("name").lower() == product_name.lower()), None)
            if match:
                product_id = match.get("id")
            else:
                # create product minimally
                sku = product_name.lower().replace(" ", "-")[:40]
                pdata = {"name": product_name, "sku": sku, "category": "imported", "description": "Imported via URL Analyzer", "keywords": []}
                created = await add_product(pdata)
                if created:
                    product_id = created[0].get("id")

        # Default product if still None: use a generic product
        if not product_id:
            # Create a generic import product if none exists
            pdata = {"name": "Imported via URL Analyzer", "sku": "imported", "category": "imported", "description": "Auto-created product for URL imports", "keywords": []}
            created = await add_product(pdata)
            if created:
                product_id = created[0].get("id")

        reviews: List[Dict[str, Any]] = []
        platform = "unknown"

        try:
            if "youtube" in hostname or "youtu.be" in hostname:
                platform = "youtube"
                # Extract video id
                vid = None
                # check query param v
                qs = parse_qs(parsed.query)
                if qs.get("v"):
                    vid = qs.get("v")[0]
                else:
                    # short url path /<id>
                    m = re.search(r"([0-9A-Za-z_-]{11})", parsed.path)
                    if m:
                        vid = m.group(1)

                if not vid:
                    # fallback: pass full url to youtube search which can extract id
                    reviews = youtube_scraper.search_video_comments(url, max_results=100)
                else:
                    reviews = youtube_scraper.search_video_comments(vid, max_results=100)

            elif "reddit" in hostname or "reddit.com" in hostname or "redd.it" in hostname:
                platform = "reddit"
                # Attempt to extract thread id from path: /r/<sub>/comments/<id>/...
                m = re.search(r"/comments/([0-9A-Za-z_]+)/", parsed.path)
                thread_id = None
                if m:
                    thread_id = m.group(1)

                # Use praw client from reddit_scraper if available
                client = getattr(reddit_scraper, "reddit", None)
                if not client:
                    raise Exception("Reddit client not available (praw not installed or not configured)")

                submission = None
                if thread_id:
                    try:
                        submission = client.submission(id=thread_id)
                    except Exception:
                        submission = None

                if not submission:
                    # Try by URL
                    try:
                        submission = client.submission(url=url)
                    except Exception as e:
                        raise Exception(f"Could not load Reddit thread: {e}")

                # Collect submission and top comments
                reviews = []
                try:
                    submission.comments.replace_more(limit=0)
                except Exception:
                    pass

                # Add the submission content as one review if text present
                try:
                    if getattr(submission, 'title', None):
                        text = (submission.title or "") + (". " + (submission.selftext or "") if getattr(submission, 'selftext', None) else "")
                        reviews.append({
                            "text": text,
                            "author": str(submission.author),
                            "platform": "reddit",
                            "source_url": f"https://reddit.com{submission.permalink}" if getattr(submission, 'permalink', None) else url,
                            "created_at": getattr(submission, 'created_utc', None)
                        })

                    for c in getattr(submission, 'comments', [])[:200]:
                        # comments.list() may be large; iterate top-level flattened
                        if getattr(c, 'body', None) and len(c.body or "") > 10:
                            reviews.append({
                                "text": c.body,
                                "author": str(getattr(c, 'author', '')),
                                "platform": "reddit",
                                "source_url": f"https://reddit.com{getattr(c, 'permalink', '')}",
                                "created_at": getattr(c, 'created_utc', None)
                            })
                except Exception as e:
                    # continue with whatever we got
                    print(f"Error iterating reddit comments: {e}")

            else:
                raise Exception("Unsupported URL platform. Only YouTube and Reddit URLs are supported.")

            # Ensure we have reviews (real scraping requirement)
            if not reviews:
                return {"status": "error", "message": "No comments/reviews found or scraping disabled for this resource."}

            # If youtube_scraper returned a list synchronously, ensure it's a list
            # If it's a coroutine (unlikely), await it
            if hasattr(reviews, "__await__"):
                reviews = await reviews

            # Run pipeline to save & analyze
            from services.data_pipeline import data_pipeline
            processed = await data_pipeline.process_reviews(reviews, product_id)
            added = len(processed)

            return {
                "status": "success",
                "platform": platform,
                "reviews_added": added,
                "product_id": product_id
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": str(e)}


url_processor = UrlProcessorService()
