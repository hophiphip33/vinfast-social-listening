from googleapiclient.discovery import build
from datetime import datetime, timedelta

class YouTubeScraper:
    def __init__(self, api_key):
        self.yt = build("youtube", "v3", developerKey=api_key)

    def search(self, keywords, max_results=25, days_back=14):
        published_after = (datetime.utcnow() - timedelta(days=days_back)).isoformat("T") + "Z"
        videos = []
        for kw in keywords:
            res = self.yt.search().list(
                q=kw, part="id,snippet", type="video",
                order="relevance", maxResults=max_results,
                publishedAfter=published_after
            ).execute()
            for it in res.get("items", []):
                vid = it["id"]["videoId"]
                videos.append({
                    "video_id": vid,
                    "title": it["snippet"]["title"],
                    "description": it["snippet"]["description"],
                    "channel": it["snippet"]["channelTitle"],
                    "published": it["snippet"]["publishedAt"],
                    "url": f"https://youtube.com/watch?v={vid}"
                })
        return videos

    def stats(self, video_ids):
        if not video_ids: return {}
        res = self.yt.videos().list(part="statistics", id=",".join(video_ids)).execute()
        out = {}
        for it in res.get("items", []):
            s = it["statistics"]
            out[it["id"]] = {
                "views": int(s.get("viewCount", 0)),
                "likes": int(s.get("likeCount", 0)),
                "comments": int(s.get("commentCount", 0))
            }
        return out
