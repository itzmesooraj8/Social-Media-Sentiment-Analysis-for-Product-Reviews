import os
import re
import asyncio
from typing import List, Dict, Any, Optional

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    _GOOGLE_AVAILABLE = True
except Exception:
    HttpError = Exception
    _GOOGLE_AVAILABLE = False


class YouTubeScraperService:
    def __init__(self):
        self.api_key = os.environ.get("YOUTUBE_API_KEY")
        self._client = None
        if not _GOOGLE_AVAILABLE:
            print("CRITICAL: google-api-python-client not installed. Install via requirements.")
            return
        if not self.api_key:
            print("CRITICAL: YOUTUBE_API_KEY missing in environment.")
            return
        try:
            self._client = build("youtube", "v3", developerKey=self.api_key)
        except Exception as e:
            print(f"YouTube client init error: {e}")

    async def search_video_comments(self, query: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Search videos by query, pick top result, fetch up to max_results comments."""
        if not self._client:
            return []

        # Run blocking requests in threadpool
        return await asyncio.to_thread(self._sync_search_comments, query, max_results)

    def _sync_search_comments(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        comments: List[Dict[str, Any]] = []
        try:
            # If query contains a video id/url, extract id
            video_id = None
            if "youtube.com" in query or "youtu.be" in query:
                m = re.search(r"(?:v=|/)([0-9A-Za-z_-]{11})", query)
                if m:
                    video_id = m.group(1)

            if not video_id:
                # search for video
                resp = self._client.search().list(q=query, part="id,snippet", type="video", maxResults=1).execute()
                items = resp.get("items") or []
                if not items:
                    return []
                video_id = items[0]["id"]["videoId"]

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
                    })
                    fetched += 1
                    if fetched >= max_results:
                        break

                page_token = resp.get("nextPageToken")
                if not page_token:
                    break

            return comments
        except HttpError as he:
            print(f"YouTube API HttpError: {he}")
            return []
        except Exception as e:
            print(f"YouTube scraping error: {e}")
            return []


youtube_scraper = YouTubeScraperService()

