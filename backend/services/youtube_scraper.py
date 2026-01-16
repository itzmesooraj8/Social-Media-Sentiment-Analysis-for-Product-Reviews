import os
import datetime
from typing import List, Dict, Any

# Graceful import for googleapiclient
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    _GOOGLE_AVAILABLE = True
except ImportError:
    build = None
    HttpError = Exception
    _GOOGLE_AVAILABLE = False


class YouTubeScraperService:
    def __init__(self):
        # Use provided key or env var
        self.api_key = os.environ.get("YOUTUBE_API_KEY", "")
        self.youtube = None
        self.enabled = False

        if not _GOOGLE_AVAILABLE:
            print("⚠️ YouTube scraping disabled: 'google-api-python-client' not installed.")
            return

        if self.api_key:
            try:
                self.youtube = build("youtube", "v3", developerKey=self.api_key)
                self.enabled = True
                print("✓ YouTube Client Initialized")
            except Exception as e:
                self.enabled = False
                print(f"❌ YouTube Client Init Failed: {e}")
        else:
            print("ℹ️ YouTube scraping disabled: YOUTUBE_API_KEY not found in environment.")

    def search_video_comments(self, query: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Search for videos matching query, then fetch comments from top video.
        """
        if not self.enabled or not self.youtube:
            # Return empty instead of crashing
            print("Debug: Attempted YouTube scrape but service is disabled.")
            return []

        try:
            video_id = None
            video_title = "Unknown Video"

            import re
            # Match standard v=VIDEO_ID or short URL /VIDEO_ID
            url_regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
            match = re.search(url_regex, query)
            
            if match and ("youtube.com" in query or "youtu.be" in query):
                video_id = match.group(1)
                
                # Fetch video title
                try:
                    vid_resp = self.youtube.videos().list(
                        part="snippet",
                        id=video_id
                    ).execute()
                    if vid_resp.get("items"):
                        video_title = vid_resp["items"][0]["snippet"]["title"]
                except Exception:
                    pass
            
            if not video_id:
                # Search for video normally
                search_response = self.youtube.search().list(
                    q=query,
                    part="id,snippet",
                    maxResults=1,
                    type="video"
                ).execute()

                if not search_response.get("items"):
                    return []

                video_id = search_response["items"][0]["id"]["videoId"]
                video_title = search_response["items"][0]["snippet"]["title"]
            
            return self._get_comments_for_video(video_id, video_title, max_results)

        except Exception as e:
            print(f"YouTube API Error: {e}")
            return []

    def _get_comments_for_video(self, video_id: str, video_title: str, max_results: int) -> List[Dict[str, Any]]:
        comments_data = []
        try:
            response = self.youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=max_results,
                textFormat="plainText"
            ).execute()

            for item in response.get("items", []):
                comment = item["snippet"]["topLevelComment"]["snippet"]
                comments_data.append({
                    "text": comment["textDisplay"],
                    "author": comment["authorDisplayName"],
                    "platform": "youtube",
                    "source_url": f"https://youtu.be/{video_id}",
                    "created_at": comment["publishedAt"],
                    "title": video_title 
                })
            
            return comments_data

        except Exception as e:
            print(f"Comment Fetch Error: {e}")
            return []

youtube_scraper = YouTubeScraperService()
