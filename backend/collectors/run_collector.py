# backend/collectors/run_collector.py
"""
Unified Social Listening Collector - 100% MIỄN PHÍ
Thu thập dữ liệu từ YouTube, Facebook, TikTok
Bao gồm: Posts, Comments, Likes, Reactions
"""

import os
import asyncio
from dotenv import load_dotenv
from datetime import datetime
from sqlalchemy import select
from database import SessionLocal, Post, Comment, init_db
from collectors.youtube_scraper import YouTubeScraper
from collectors.facebook_scraper import FacebookScraper, FacebookGroupScraper
from collectors.tiktok_scraper import TikTokScraper
from sentiment.analyzer import SentimentAnalyzer

load_dotenv()

# Configuration
YT_API_KEY = os.getenv("YT_API_KEY")
FB_COOKIES_FILE = os.getenv("FB_COOKIES_FILE", None)  # Optional

KEYWORDS = [
    "VinFast", "VF8", "VF9", "VFe34", 
    "xe điện VinFast", "VinFast review", 
    "lỗi VinFast"
]

TIKTOK_HASHTAGS = ["vinfast", "vf8", "vf9", "xedien", "xedienvietnam"]
TIKTOK_USERS = ["vinfastauto"]  # Official TikTok accounts to monitor


def upsert_post(db, data, platform):
    """Insert hoặc update post, trả về (post, is_new)"""
    exists = db.execute(
        select(Post).where(Post.post_id == data["post_id"])
    ).scalar_one_or_none()
    
    if exists:
        return exists, False
    
    post = Post(
        platform=platform,
        post_id=data["post_id"],
        author=data.get("author", ""),
        content=data["content"],
        published_date=data["published_date"],
        likes=data.get("likes", 0),
        shares=data.get("shares", 0),
        comments_count=data.get("comments_count", 0),
        url=data.get("url", ""),
        extra_data=data.get("extra_data", {})  # Lưu reactions, views, etc.
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post, True


def save_comments(db, post_id, comments_list, analyzer):
    """Lưu comments và phân tích sentiment"""
    saved_count = 0
    
    for comment_data in comments_list:
        # Check duplicate
        exists = db.execute(
            select(Comment).where(Comment.comment_id == comment_data["comment_id"])
        ).scalar_one_or_none()
        
        if exists:
            continue
        
        # Phân tích sentiment của comment
        sentiment_result = analyzer.analyze_one(comment_data["text"])
        
        comment = Comment(
            post_id=post_id,
            comment_id=comment_data["comment_id"],
            author=comment_data.get("author", ""),
            content=comment_data["text"],
            likes=comment_data.get("likes", 0),
            created_at=comment_data.get("time") or comment_data.get("created_time"),
            sentiment=sentiment_result["label"],
            sentiment_score=sentiment_result["score"]
        )
        
        db.add(comment)
        saved_count += 1
    
    if saved_count > 0:
        db.commit()
    
    return saved_count


def process_sentiment(db, post, analyzer):
    """Phân tích cảm xúc của post"""
    result = analyzer.analyze_one(post.content)
    
    # Update post với sentiment
    post.sentiment = result["label"]
    post.sentiment_score = result["score"]
    db.commit()


def collect_youtube(db, analyzer, days_back=14, max_results=20):
    """Thu thập từ YouTube"""
    print("\n📹 Collecting YouTube videos...")
    
    if not YT_API_KEY:
        print("⚠️  YouTube API key not found. Skipping.")
        return 0, 0
    
    scraper = YouTubeScraper(YT_API_KEY)
    videos = scraper.search(KEYWORDS, max_results=max_results, days_back=days_back)
    
    video_ids = [v["video_id"] for v in videos]
    stats = scraper.stats(video_ids)
    
    new_posts = 0
    new_comments = 0
    
    for video in videos:
        content = f"{video['title']} {video['description']}".strip()
        
        data = {
            "post_id": video["video_id"],
            "author": video["channel"],
            "content": content,
            "published_date": datetime.fromisoformat(video["published"].replace("Z", "+00:00")),
            "likes": stats.get(video["video_id"], {}).get("likes", 0),
            "shares": 0,
            "comments_count": stats.get(video["video_id"], {}).get("comments", 0),
            "url": video["url"],
            "extra_data": {
                "views": stats.get(video["video_id"], {}).get("views", 0),
                "platform_type": "video"
            }
        }
        
        post, is_new = upsert_post(db, data, "youtube")
        
        if is_new:
            new_posts += 1
            process_sentiment(db, post, analyzer)
        
        # TODO: Lấy YouTube comments (cần thêm API call)
        # comments = scraper.get_comments(video["video_id"])
        # new_comments += save_comments(db, post.id, comments, analyzer)
    
    print(f"✅ YouTube: {new_posts} posts, {new_comments} comments")
    return new_posts, new_comments


def collect_facebook(db, analyzer, days_back=14, max_posts=30):
    """Thu thập từ Facebook - Pages công khai"""
    print("\n👍 Collecting Facebook posts...")
    
    scraper = FacebookScraper(cookies_file=FB_COOKIES_FILE)
    posts_list = scraper.search_posts_by_keywords(
        KEYWORDS, 
        days_back=days_back, 
        max_posts_per_page=max_posts
    )
    
    new_posts = 0
    new_comments = 0
    
    for post_data in posts_list:
        data = {
            "post_id": post_data["post_id"],
            "author": post_data["author"],
            "content": post_data["content"],
            "published_date": post_data["published"],
            "likes": post_data.get("total_reactions", 0),
            "shares": post_data.get("shares", 0),
            "comments_count": post_data.get("comments_count", 0),
            "url": post_data["url"],
            "extra_data": {
                "reactions": {
                    "like": post_data.get("likes", 0),
                    "love": post_data.get("love", 0),
                    "haha": post_data.get("haha", 0),
                    "wow": post_data.get("wow", 0),
                    "sad": post_data.get("sad", 0),
                    "angry": post_data.get("angry", 0)
                },
                "has_image": bool(post_data.get("image")),
                "has_video": bool(post_data.get("video"))
            }
        }
        
        post, is_new = upsert_post(db, data, "facebook")
        
        if is_new:
            new_posts += 1
            process_sentiment(db, post, analyzer)
        
        # Lưu comments
        if post_data.get("comments"):
            new_comments += save_comments(db, post.id, post_data["comments"], analyzer)
    
    print(f"✅ Facebook: {new_posts} posts, {new_comments} comments")
    return new_posts, new_comments


def collect_facebook_groups(db, analyzer, days_back=7, max_posts=20):
    """Thu thập từ Facebook PUBLIC Groups"""
    print("\n👥 Collecting Facebook Group posts...")
    
    # Danh sách các public groups liên quan
    public_groups = [
        # "VinFastOwnersVietnam",  # Nếu public
        # "XeDienVietnam",
        # "MuaXeDienVietnam"
    ]
    
    group_scraper = FacebookGroupScraper(cookies_file=FB_COOKIES_FILE)
    new_posts = 0
    new_comments = 0
    
    for group_id in public_groups:
        try:
            posts_list = group_scraper.get_group_posts(
                group_id,
                keywords=KEYWORDS,
                days_back=days_back,
                max_posts=max_posts
            )
            
            for post_data in posts_list:
                data = {
                    "post_id": post_data["post_id"],
                    "author": post_data["author"],
                    "content": post_data["content"],
                    "published_date": post_data["published"],
                    "likes": post_data.get("total_reactions", 0),
                    "shares": post_data.get("shares", 0),
                    "comments_count": post_data.get("comments_count", 0),
                    "url": post_data["url"],
                    "extra_data": {"group_id": group_id, "source": "group"}
                }
                
                post, is_new = upsert_post(db, data, "facebook_group")
                
                if is_new:
                    new_posts += 1
                    process_sentiment(db, post, analyzer)
                
                if post_data.get("comments"):
                    new_comments += save_comments(db, post.id, post_data["comments"], analyzer)
        
        except Exception as e:
            print(f"  ⚠️  Error with group {group_id}: {e}")
    
    print(f"✅ Facebook Groups: {new_posts} posts, {new_comments} comments")
    return new_posts, new_comments


async def collect_tiktok(db, analyzer, days_back=14, max_results=30):
    """Thu thập từ TikTok"""
    print("\n🎵 Collecting TikTok videos...")
    
    scraper = TikTokScraper()
    new_posts = 0
    new_comments = 0
    
    async with scraper.api:
        # Thu thập từ keyword
        videos_list = await scraper.search_videos_by_keyword(
            KEYWORDS,
            days_back=days_back,
            max_results=max_results
        )
        
        for video_data in videos_list:
            data = {
                "post_id": video_data["video_id"],
                "author": video_data["author"],
                "content": video_data["content"],
                "published_date": video_data["published"],
                "likes": video_data.get("likes", 0),
                "shares": video_data.get("shares", 0),
                "comments_count": video_data.get("comments_count", 0),
                "url": video_data["url"],
                "extra_data": {
                    "views": video_data.get("views", 0),
                    "author_name": video_data.get("author_name", ""),
                    "hashtags": video_data.get("hashtags", []),
                    "platform_type": "video"
                }
            }
            
            post, is_new = upsert_post(db, data, "tiktok")
            
            if is_new:
                new_posts += 1
                process_sentiment(db, post, analyzer)
            
            # Lưu comments
            if video_data.get("comments"):
                new_comments += save_comments(db, post.id, video_data["comments"], analyzer)
        
        # Thu thập từ hashtags
        videos_hashtags = await scraper.search_by_hashtag(
            TIKTOK_HASHTAGS,
            days_back=days_back,
            max_results=max_results
        )
        
        for video_data in videos_hashtags:
            data = {
                "post_id": video_data["video_id"],
                "author": video_data["author"],
                "content": video_data["content"],
                "published_date": video_data["published"],
                "likes": video_data.get("likes", 0),
                "shares": video_data.get("shares", 0),
                "comments_count": video_data.get("comments_count", 0),
                "url": video_data["url"],
                "extra_data": {
                    "views": video_data.get("views", 0),
                    "author_name": video_data.get("author_name", ""),
                    "hashtags": video_data.get("hashtags", [])
                }
            }
            
            post, is_new = upsert_post(db, data, "tiktok")
            
            if is_new:
                new_posts += 1
                process_sentiment(db, post, analyzer)
            
            if video_data.get("comments"):
                new_comments += save_comments(db, post.id, video_data["comments"], analyzer)
    
    print(f"✅ TikTok: {new_posts} videos, {new_comments} comments")
    return new_posts, new_comments


async def main():
    """Main collector function"""
    print("\n" + "="*70)
    print("🚀 SOCIAL LISTENING COLLECTOR - VinFast Monitoring")
    print("="*70)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔍 Keywords: {', '.join(KEYWORDS)}")
    
    # Initialize
    init_db()
    db = SessionLocal()
    analyzer = SentimentAnalyzer()
    
    total_posts = 0
    total_comments = 0
    
    try:
        # YouTube
        posts, comments = collect_youtube(db, analyzer, days_back=14, max_results=20)
        total_posts += posts
        total_comments += comments
        
        # Facebook Pages
        posts, comments = collect_facebook(db, analyzer, days_back=14, max_posts=30)
        total_posts += posts
        total_comments += comments
        
        # Facebook Groups
        posts, comments = collect_facebook_groups(db, analyzer, days_back=7, max_posts=20)
        total_posts += posts
        total_comments += comments
        
        # TikTok
        posts, comments = await collect_tiktok(db, analyzer, days_back=14, max_results=30)
        total_posts += posts
        total_comments += comments
        
    except Exception as e:
        print(f"\n❌ Error during collection: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print("\n" + "="*70)
    print(f"✨ Collection Complete!")
    print(f"📊 Total new posts: {total_posts}")
    print(f"💬 Total new comments: {total_comments}")
    print(f"⏰ Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())