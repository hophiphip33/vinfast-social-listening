import os
from dotenv import load_dotenv
from datetime import datetime
from sqlalchemy import select
from database import SessionLocal, Post, ProcessedPost, init_db
from collectors.youtube_scraper import YouTubeScraper
from sentiment.analyzer import SentimentAnalyzer

load_dotenv()
API_KEY = os.getenv("YT_API_KEY")
KEYWORDS = ["VinFast", "VF8", "VF9", "VFe34", "xe điện VinFast", "VinFast review", "lỗi VinFast"]

def upsert_post(db, data):
    # dedupe theo post_id (dùng video_id)
    exists = db.execute(select(Post).where(Post.post_id == data["post_id"])).scalar_one_or_none()
    if exists: return exists
    p = Post(
        platform="youtube",
        post_id=data["post_id"],
        author=data.get("author"),
        content=data["content"],
        published_date=data["published_date"],
        likes=data.get("likes", 0),
        shares=0,
        comments_count=data.get("comments", 0),
        url=data.get("url")
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

def main():
    init_db()
    yt = YouTubeScraper(API_KEY)
    analyzer = SentimentAnalyzer()
    db = SessionLocal()

    vids = yt.search(KEYWORDS, max_results=20, days_back=14)
    id_list = [v["video_id"] for v in vids]
    stats = yt.stats(id_list)

    inserted = 0
    for v in vids:
        content = f"{v['title']} {v['description']}".strip()
        data = {
            "post_id": v["video_id"],
            "author": v["channel"],
            "content": content,
            "published_date": datetime.fromisoformat(v["published"].replace("Z","+00:00")),
            "likes": stats.get(v["video_id"],{}).get("likes",0),
            "comments": stats.get(v["video_id"],{}).get("comments",0),
            "url": v["url"]
        }
        post = upsert_post(db, data)
        if post and not post.processed:
            res = analyzer.one(content)
            proc = ProcessedPost(
                post_id=post.id,
                sentiment=res["label"],
                sentiment_score=res["score"]
            )
            db.add(proc)
            db.commit()
            inserted += 1

    db.close()
    print(f"Done. Inserted/processed: {inserted}")

if __name__ == "__main__":
    main()
