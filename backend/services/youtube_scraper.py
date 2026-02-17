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
        self.api_key = os.environ.get("YOUTUBE_API_KEY", "").strip()
        self._client = None
        
        if _GOOGLE_AVAILABLE and self.api_key:
            try:
                self._client = build("youtube", "v3", developerKey=self.api_key)
                logger.info("YouTube: API Client initialized successfully.")
            except Exception as e:
                logger.error(f"YouTube client init error: {e}")
                self._client = None
        elif not _GOOGLE_AVAILABLE:
            logger.warning("YouTube: Google API Client not installed. YouTube scraping disabled.")
        elif not self.api_key:
            logger.warning("YouTube: No API Key found. YouTube scraping disabled.")

    async def reload_config(self):
        """Reload configuration from environment variables."""
        self.api_key = os.environ.get("YOUTUBE_API_KEY", "").strip()
        logger.info(f"YouTube: Reloading config with key: {self.api_key[:10]}...")
        
        if _GOOGLE_AVAILABLE and self.api_key:
            try:
                # We need to rebuild the client
                self._client = build("youtube", "v3", developerKey=self.api_key)
                logger.info("YouTube: Config reloaded. Client initialized.")
            except Exception as e:
                logger.error(f"YouTube re-init error: {e}")
                self._client = None
        else:
            self._client = None
            logger.info("YouTube: API Key missing or lib unavailable after reload.")

    async def search_video_comments(self, query: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Search videos by query (requires API), pick top result, fetch comments.
        """
        # Run blocking requests in threadpool
        return await asyncio.to_thread(self._sync_search_comments, query, max_results)

    async def scrape_video_comments(self, video_url: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Directly scrape comments from a specific video URL."""
        return await self.search_video_comments(video_url, max_results)

    def _get_video_ids_sync(self, query: str, max_videos: int = 3) -> List[str]:
        video_ids = []
        if "youtube.com" in query or "youtu.be" in query:
            m = re.search(r"(?:v=|/)([0-9A-Za-z_-]{11})", query)
            if m:
                return [m.group(1)]

        if self._client:
            try:
                resp = self._client.search().list(q=query, part="id,snippet", type="video", maxResults=max_videos).execute()
                items = resp.get("items") or []
                for item in items:
                    v_id = item.get("id", {}).get("videoId")
                    if v_id:
                        video_ids.append(v_id)
            except HttpError as he:
                if he.resp.status in [400, 403]:
                    logger.warning(f"YouTube search failed {he.resp.status}: Invalid API Key or Quota Exceeded.")
                    self._client = None
                else: 
                     logger.error(f"YouTube HTTP search error: {he}")
            except Exception as e:
                logger.error(f"YouTube search error: {e}")
        return video_ids

    def _sync_search_comments(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Sync implementation using API. Tries multiple videos if needed."""
        all_comments: List[Dict[str, Any]] = []
        
        if not self._client:
            logger.warning("YouTube API client not initialized.")
            return []

        # 1. Get multiple Video IDs to increase chance of finding comments
        video_ids = self._get_video_ids_sync(query, max_videos=5)
        if not video_ids:
            logger.warning(f"Could not find any videos for query: {query}")
            return []

        for video_id in video_ids:
            try:
                logger.info(f"Fetching comments for Video ID: {video_id}")
                fetched = 0
                page_token = None
                video_comments = []
                
                # Fetch up to 50 comments per video, or until we hit global max_results
                limit_for_this_video = min(50, max_results - len(all_comments))
                if limit_for_this_video <= 0:
                    break

                while fetched < limit_for_this_video:
                    params = {
                        "part": "snippet",
                        "videoId": video_id,
                        "maxResults": min(100, limit_for_this_video - fetched),
                        "textFormat": "plainText",
                    }
                    if page_token:
                        params["pageToken"] = page_token

                    resp = self._client.commentThreads().list(**params).execute()
                    items = resp.get("items", [])
                    if not items:
                        break

                    for item in items:
                        top = item["snippet"]["topLevelComment"]["snippet"]
                        video_comments.append({
                            "content": top.get("textDisplay"),
                            "author": top.get("authorDisplayName") or top.get("authorOriginal"),
                            "platform": "youtube",
                            "source_url": f"https://youtu.be/{video_id}",
                            "created_at": top.get("publishedAt"),
                            "like_count": top.get("likeCount", 0),
                            "reply_count": item["snippet"].get("totalReplyCount", 0)
                        })
                        fetched += 1
                        if fetched >= limit_for_this_video:
                            break

                    page_token = resp.get("nextPageToken")
                    if not page_token:
                        break

                all_comments.extend(video_comments)
                logger.info(f"Found {len(video_comments)} comments in video {video_id}")
                
                if len(all_comments) >= max_results:
                    break
                    
            except HttpError as he:
                if he.resp.status in [400, 401, 403]:
                    logger.warning(f"YouTube API Error {he.resp.status}: Invalid Key or Quota Exceeded. disabling.")
                    self._client = None  # Disable client to prevent further errors
                    break
                else:
                    logger.error(f"YouTube HTTP Error: {he}")
            except Exception as e:
                # If comments are disabled, we might get an HttpError. Skip to next video.
                logger.warning(f"YouTube search error for video {video_id}: {e}")
                continue

        return all_comments

    async def search_video_comments_stream(self, query: str, max_results: int = 50):
        """
        True Async generator for streaming comments page-by-page.
        Yields comments as soon as they are fetched from the API.
        """
        if not self._client:
             logger.warning("YouTube API client missing")
             return

        # 1. Get Video IDs (Blocking call in thread)
        video_ids = await asyncio.to_thread(self._get_video_ids_sync, query, 3)
        
        if not video_ids:
            logger.warning(f"Could not find video for query: {query}")
            return

        # 2. Paginate and Yield
        total_fetched = 0
        
        for video_id in video_ids:
            if total_fetched >= max_results:
                break
                
            fetched_this_video = 0
            page_token = None
            limit_this_video = min(50, max_results - total_fetched)
            
            while fetched_this_video < limit_this_video:
                try:
                    # Fetch one page
                    params = {
                        "part": "snippet",
                        "videoId": video_id,
                        "maxResults": min(100, limit_this_video - fetched_this_video),
                        "textFormat": "plainText",
                    }
                    if page_token:
                        params["pageToken"] = page_token

                    # Execute in thread to avoid blocking event loop
                    resp = await asyncio.to_thread(
                        lambda: self._client.commentThreads().list(**params).execute()
                    )
                    
                    items = resp.get("items", [])
                    if not items:
                        break

                    for item in items:
                        top = item["snippet"]["topLevelComment"]["snippet"]
                        comment = {
                            "content": top.get("textDisplay"),
                            "author": top.get("authorDisplayName") or top.get("authorOriginal"),
                            "platform": "youtube",
                            "source_url": f"https://youtu.be/{video_id}",
                            "created_at": top.get("publishedAt"),
                            "like_count": top.get("like_count", 0),
                            "reply_count": item["snippet"].get("totalReplyCount", 0)
                        }
                        yield comment
                        fetched_this_video += 1
                        total_fetched += 1
                        if total_fetched >= max_results or fetched_this_video >= limit_this_video:
                            break
                    
                    page_token = resp.get("nextPageToken")
                    if not page_token:
                        break
                        
                except HttpError as he:
                    if he.resp.status == 403:
                        logger.warning(f"Comments disabled for video {video_id}")
                        break # Skip this video
                    logger.error(f"YouTube Stream HttpError: {he}")
                    break
                except Exception as e:
                    logger.error(f"YouTube Stream Error: {e}")
                    break

youtube_scraper = YouTubeScraperService()