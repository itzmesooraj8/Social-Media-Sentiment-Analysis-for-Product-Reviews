import os
import re
import asyncio
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    _GOOGLE_AVAILABLE = True
except Exception:
    HttpError = Exception
    _GOOGLE_AVAILABLE = False

try:
    from youtube_comment_downloader import YoutubeCommentDownloader, SORT_BY_POPULAR
    _YCD_AVAILABLE = True
except ImportError:
    _YCD_AVAILABLE = False


class YouTubeScraperService:
    def __init__(self):
        self.api_key = os.environ.get("YOUTUBE_API_KEY")
        self._client = None
        
        if _GOOGLE_AVAILABLE and self.api_key:
            try:
                self._client = build("youtube", "v3", developerKey=self.api_key)
            except Exception as e:
                logger.error(f"YouTube client init error: {e}")
        elif not _GOOGLE_AVAILABLE:
            logger.warning("YouTube: Google API Client not installed. YouTube scraping disabled.")
        elif not self.api_key:
            logger.warning("YouTube: No API Key found. YouTube scraping disabled.")

    async def search_video_comments(self, query: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Search videos by query (requires API), pick top result, fetch comments.
        """
        # Run blocking requests in threadpool
        return await asyncio.to_thread(self._sync_search_comments, query, max_results)

    async def scrape_video_comments(self, video_url: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Directly scrape comments from a specific video URL."""
        return await self.search_video_comments(video_url, max_results)

    def _get_video_id_sync(self, query: str) -> Optional[str]:
        video_id = None
        if "youtube.com" in query or "youtu.be" in query:
            m = re.search(r"(?:v=|/)([0-9A-Za-z_-]{11})", query)
            if m:
                video_id = m.group(1)

        if not video_id and self._client:
            try:
                resp = self._client.search().list(q=query, part="id,snippet", type="video", maxResults=1).execute()
                items = resp.get("items") or []
                if not items:
                    return None
                video_id = items[0]["id"]["videoId"]
            except Exception as e:
                logger.error(f"YouTube search error: {e}")
                return None
        return video_id

    def _sync_search_comments(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Sync implementation using API."""
        comments: List[Dict[str, Any]] = []
        
        if not self._client:
            logger.warning("YouTube API missing.")
            return []

        # 1. Get Video ID
        video_id = self._get_video_id_sync(query)
        if not video_id:
            logger.warning(f"Could not find video for query: {query}")
            return []

        try:
            # paginate commentThreads
            fetched = 0
            page_token = None
            while fetched < max_results:
                params = {
                    "part": "snippet",
                    "videoId": video_id,
                    "maxResults": min(100, max_results - fetched),
                    "textFormat": "plainText",
                }
                if page_token:
                    params["pageToken"] = page_token

                resp = self._client.commentThreads().list(**params).execute()
                for item in resp.get("items", []):
                    top = item["snippet"]["topLevelComment"]["snippet"]
                    comments.append({
                        "content": top.get("textDisplay"),
                        "author": top.get("authorDisplayName") or top.get("authorOriginal"),
                        "platform": "youtube",
                        "source_url": f"https://youtu.be/{video_id}",
                        "created_at": top.get("publishedAt"),
                        "like_count": top.get("likeCount", 0),
                        "reply_count": item["snippet"].get("totalReplyCount", 0)
                    })
                    fetched += 1
                    if fetched >= max_results:
                        break

                page_token = resp.get("nextPageToken")
                if not page_token:
                    break

            return comments
        except HttpError as he:
            logger.error(f"YouTube API HttpError: {he}")
            return []
        except Exception as e:
            logger.error(f"YouTube scraping error: {e}")
            return []

    async def search_video_comments_stream(self, query: str, max_results: int = 50):
        """
        Async generator for streaming comments.
        """
        # Fallback to API (Not truly streaming usually, but we can simulate)
        if self._client:
            # Just fetch all and yield one by one
            items = await self.search_video_comments(query, max_results)
            for item in items:
                yield item

youtube_scraper = YouTubeScraperService()