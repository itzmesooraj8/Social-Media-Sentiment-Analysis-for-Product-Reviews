import os
import datetime
from typing import List, Dict, Any
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class YouTubeScraperService:
    def __init__(self):
        # Use provided key or env var
        self.api_key = os.environ.get("YOUTUBE_API_KEY", "")
        self.youtube = None
        if self.api_key:
            try:
                self.youtube = build("youtube", "v3", developerKey=self.api_key)
                print("✓ YouTube Client Initialized")
            except Exception as e:
                print(f"YouTube Client Init Failed: {e}")

    def search_video_comments(self, query: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Search for videos matching query, then fetch comments from top video.
        If query is a URL, extract video_id directly.
        """
        if not self.youtube:
             raise Exception("YouTube API Key missing/invalid. Cannot scrape.")

        try:
            video_id = None
            video_title = "Unknown Video"

            # Check if query is a URL
            import re
            # Match standard v=VIDEO_ID or short URL /VIDEO_ID
            # Standard: youtube.com/watch?v=...
            # Short: youtu.be/...
            url_regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
            match = re.search(url_regex, query)
            
            if match and ("youtube.com" in query or "youtu.be" in query):
                video_id = match.group(1)
                print(f"Detected YouTube URL. extracting ID: {video_id}")
                
                # Fetch video title for context
                vid_resp = self.youtube.videos().list(
                    part="snippet",
                    id=video_id
                ).execute()
                if vid_resp.get("items"):
                    video_title = vid_resp["items"][0]["snippet"]["title"]
            
            if not video_id:
                # 1. Search for video normally
                print(f"Searching YouTube for: {query}")
                search_response = self.youtube.search().list(
                    q=query,
                    part="id,snippet",
                    maxResults=1,
                    type="video"
                ).execute()

                if not search_response.get("items"):
                    print("No video found.")
                    return []

                video_id = search_response["items"][0]["id"]["videoId"]
                video_title = search_response["items"][0]["snippet"]["title"]
            
            print(f"Found Video: {video_title} ({video_id})")

            # 2. Get Comments
            return self._get_comments_for_video(video_id, video_title, max_results)

        except HttpError as e:
            print(f"YouTube API Error: {e}")
            raise Exception(f"YouTube API Error: {e.reason}")

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
                text = comment["textDisplay"]
                author = comment["authorDisplayName"]
                published_at = comment["publishedAt"]
                
                comments_data.append({
                    "text": text,
                    "author": author,
                    "platform": "youtube",
                    "source_url": f"https://youtu.be/{video_id}",
                    "created_at": published_at,
                    "title": video_title 
                })
            
            return comments_data

        except HttpError as e:
            print(f"Comment Fetch Error: {e}")
            if e.resp.status == 403:
                # Comments might be disabled
                print("Comments disabled for this video.")
                return []
            raise

youtube_scraper = YouTubeScraperService()
