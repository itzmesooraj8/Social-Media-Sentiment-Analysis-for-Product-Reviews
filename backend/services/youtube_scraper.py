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
        self._downloader = None

        if _GOOGLE_AVAILABLE and self.api_key:
            try:
                self._client = build("youtube", "v3", developerKey=self.api_key)
            except Exception as e:
                logger.error(f"YouTube client init error: {e}")
        
        if _YCD_AVAILABLE:
            self._downloader = YoutubeCommentDownloader()

    async def search_video_comments(self, query: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Search videos by query (requires API), pick top result, fetch comments.
        """
        # Run blocking requests in threadpool
        return await asyncio.to_thread(self._sync_search_comments, query, max_results)

    async def scrape_video_comments(self, video_url: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Directly scrape comments from a specific video URL."""
        # If we have the URL, we can use the downloader even without API key
        if self._downloader:
             return await asyncio.to_thread(self._sync_scrape_ycd, video_url, max_results)
        
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

    def _sync_scrape_ycd(self, video_url: str, max_results: int) -> List[Dict[str, Any]]:
        """Scrape using youtube-comment-downloader (No API Key needed)"""
        results = []
        try:
            generator = self._downloader.get_comments_from_url(video_url, sort_by=SORT_BY_POPULAR)
            for comment in generator:
                results.append({
                    "content": comment.get('text'),
                    "author": comment.get('author'),
                    "platform": "youtube",
                    "source_url": video_url,
                    "created_at": comment.get('time'), # Relative time usually
                    "like_count": comment.get('votes', 0), # 'votes' usually string, might need parsing
                    "reply_count": 0
                })
                if len(results) >= max_results:
                    break
        except Exception as e:
            logger.error(f"YCD Scrape error: {e}")
        
        return results

    def _sync_search_comments(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Sync implementation using API."""
        comments: List[Dict[str, Any]] = []
        
        # 1. Get Video ID
        video_id = self._get_video_id_sync(query)
        if not video_id:
            logger.warning(f"Could not find video for query: {query}")
            return []

        # 2. If we have downloader, prefer it for comments (cheaper/better)
        if self._downloader:
            return self._sync_scrape_ycd(f"https://www.youtube.com/watch?v={video_id}", max_results)

        # 3. Fallback to API if downloader missing
        if not self._client:
            logger.warning("YouTube API missing and Downloader missing.")
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
                        "author": top.get("authorDisplayName"),
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


youtube_scraper = YouTubeScraperService()