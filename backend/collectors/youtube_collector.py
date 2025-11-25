"""
YouTube Video Collector - Top 20 Most Viewed (30 Days)
Fixed: Handle videos with disabled comments (NoneType error)
"""

import os
import sys
import asyncio
import requests
import concurrent.futures
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple

# --- IMPORT CÁC MODULE DATABASE ---
from backend.database.connection import DatabaseOperations, db_manager 
from backend.processors.vietnamese_sentiment import VietnameseSentimentAnalyzer
from backend.config.settings import settings

from yt_dlp import YoutubeDL
from youtube_transcript_api import YouTubeTranscriptApi
from loguru import logger
import google.generativeai as genai

# --- CẤU HÌNH GEMINI ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBpWUHLIE41s3ZdM_aJhGZ5vJjkvOxo2ik")
if not GEMINI_API_KEY:
    logger.warning("⚠️ GEMINI_API_KEY not found. Summarization will be skipped.")
else:
    genai.configure(api_key=GEMINI_API_KEY)

gemini_model = genai.GenerativeModel('gemini-2.5-flash')
executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

VINGROUP_KEYWORDS = [
    "vingroup", "phạm nhật vượng", "vinfast", "xe điện vinfast", 
    "vinhomes", "vinpearl", "vinmec", "vf8", "vf9", "vf3","vinspeed",
    "vinbus", "vincom", "vinmart", "vinmart+", "vinid", "vinwonders",
    "vinpearl land", "vinpearl safari", "vinpearl golf", "vinpearl resort","vinspace"
]

# ==============================================================================
# 1. CÁC HÀM HỖ TRỢ (HELPER FUNCTIONS)
# ==============================================================================

def gemini_summarize_sync(text, max_words=500):
    if not text or not GEMINI_API_KEY: return None
    try:
        text = text[:10000]
        prompt = f"""Hãy tóm tắt nội dung sau đây thành khoảng {max_words} từ. 
Tập trung vào những điểm chính và thông tin quan trọng nhất.
Trả lời bằng Tiếng Việt.

Nội dung:
{text}

Tóm tắt:"""
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"⚠️ Gemini summarization failed: {e}")
        return None

def get_dislikes_sync(video_id):
    try:
        url = f"https://returnyoutubedislikeapi.com/votes?videoId={video_id}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            return resp.json().get("dislikes", 0)
    except:
        pass
    return 0

def get_transcript_sync(video_id):
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list_transcripts(video_id)
        
        # 1. Tiếng Việt
        try:
            t = transcript_list.find_transcript(['vi'])
            return " ".join([item['text'] for item in t.fetch()]), "youtube-vi"
        except: pass
        
        # 2. Dịch sang Tiếng Việt
        try:
            t = transcript_list.find_transcript(['en', 'en-US']).translate('vi')
            return " ".join([item['text'] for item in t.fetch()]), "youtube-translated-vi"
        except: pass

        # 3. Fallback
        for t in transcript_list:
            if t.is_translatable:
                return " ".join([item['text'] for item in t.translate('vi').fetch()]), "youtube-auto-translated"
            return " ".join([item['text'] for item in t.fetch()]), f"youtube-{t.language_code}"
            
    except Exception:
        return "", ""
    return "", ""

async def gemini_summarize(text, max_words=500):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, gemini_summarize_sync, text, max_words)

async def get_dislikes(video_id):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, get_dislikes_sync, video_id)

async def get_transcript(video_id):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, get_transcript_sync, video_id)

def _convert_timestamp(ts: Any) -> datetime:
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts)
    if isinstance(ts, str):
        try: return datetime.strptime(ts, '%Y%m%d')
        except: pass
    return datetime.now()

# ==============================================================================
# 2. CORE LOGIC
# ==============================================================================

async def get_video_details_and_save(db_ops, url, analyzer):
    loop = asyncio.get_running_loop()
    
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'skip_download': True,
        'getcomments': True,
        'ignoreerrors': True, # Bỏ qua lỗi nếu video bị xóa/private giữa chừng
        'extractor_args': {'youtube': {'max_comments': ['100'], 'comment_sort': ['top']}},
    }

    # 1. Lấy Metadata
    try:
        def fetch_meta():
            with YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        info = await loop.run_in_executor(executor, fetch_meta)
    except Exception as e:
        logger.error(f"Skipping {url}: {e}")
        return False

    if not info: return False
    video_id = info.get('id')
    
    # 2. Lấy Transcript & Summary
    transcript_text, _ = await get_transcript(video_id)
    summary = ""
    if transcript_text:
        summary = await gemini_summarize(transcript_text, max_words=300)
    elif info.get('description'):
        summary = await gemini_summarize(info.get('description'), max_words=200)

    # 3. Dislikes
    dislikes = await get_dislikes(video_id)

    # 4. Lưu Post
    post_data = {
        "platform": "youtube",
        "source_url": url,
        "source_name": info.get('uploader', 'YouTube'),
        "title": info.get('title', 'No Title'),
        "content": summary if summary else info.get('description', ''),
        "original_transcript": transcript_text[:1000] + "..." if len(transcript_text) > 1000 else transcript_text,
        "views_count": info.get("view_count", 0),
        "likes_count": info.get("like_count", 0),
        "dislikes_count": dislikes,
        "comments_count": info.get("comment_count", 0),
        "published_at": _convert_timestamp(info.get('upload_date')),
        "collected_at": datetime.now(),
        "language": "vi",
        "is_processed": True
    }

    post_id = await db_ops.insert_post(post_data)
    if not post_id: return False

    # 5. Xử lý Comment (SỬA LỖI TẠI ĐÂY)
    # info.get('comments') có thể là None nếu video tắt comment
    raw_comments = info.get('comments') or [] 
    
    if raw_comments:
        # Chỉ sort nếu list không rỗng
        try:
            raw_comments.sort(key=lambda x: x.get('like_count', 0) or 0, reverse=True)
        except Exception as e:
            logger.warning(f"Error sorting comments for {video_id}: {e}")

        saved_comments = 0
        for c in raw_comments[:20]:
            if not c.get('text'): continue
            try:
                sent = await analyzer.analyze_sentiment(c['text'])
                comment_doc = {
                    "post_id": post_id,
                    "author": c.get('author'),
                    "content": c.get('text'),
                    "likes_count": c.get('like_count', 0),
                    "published_at": _convert_timestamp(c.get('timestamp')),
                    "collected_at": datetime.now(),
                    "sentiment": sent["sentiment"],
                    "sentiment_score": sent["sentiment_score"]
                }
                await db_ops.insert_comment(comment_doc)
                saved_comments += 1
            except: continue
        logger.info(f"✅ Saved: {post_data['title'][:50]}... (V:{post_data['views_count']}, C:{saved_comments})")
    else:
        logger.info(f"✅ Saved: {post_data['title'][:50]}... (Comments disabled/empty)")
        
    return True

async def search_and_collect_top_20_videos():
    db_ops = DatabaseOperations()
    analyzer = VietnameseSentimentAnalyzer()
    
    days_ago_30 = datetime.now() - timedelta(days=30)
    date_str = days_ago_30.strftime('%Y%m%d')
    
    # Tìm kiếm rộng hơn để lọc
    query = " | ".join(VINGROUP_KEYWORDS[:5])
    logger.info(f"🚀 Searching videos since {date_str}...")
    
    ydl_search_opts = {
        'quiet': True,
        'extract_flat': True,
        'dateafter': date_str,
    }
    
    loop = asyncio.get_running_loop()
    found_entries = []
    
    try:
        def run_search():
            with YoutubeDL(ydl_search_opts) as ydl:
                # Tìm 60 video để lọc ra 20 video cao nhất
                return ydl.extract_info(f"ytsearch60:{query}", download=False)
        
        info = await loop.run_in_executor(executor, run_search)
        if 'entries' in info:
            found_entries = [e for e in info['entries'] if e]
    except Exception as e:
        logger.error(f"Search error: {e}")
        return 0

    # Lọc & Sắp xếp
    valid_videos = []
    for vid in found_entries:
        # Đảm bảo view_count là số
        view_count = vid.get('view_count')
        if view_count is None: view_count = 0
        vid['view_count'] = view_count # Gán lại để sort an toàn
        valid_videos.append(vid)

    valid_videos.sort(key=lambda x: x['view_count'], reverse=True)
    top_20_videos = valid_videos[:20]
    
    logger.info(f"🎯 Top 20 videos identified. Collecting details...")

    count = 0
    for vid in top_20_videos:
        url = vid.get('url')
        if await db_ops.get_post_by_url(url):
            logger.info(f"Skipping existing: {url}")
            continue
            
        try:
            success = await get_video_details_and_save(db_ops, url, analyzer)
            if success:
                count += 1
                await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"Error processing video {url}: {e}")
            continue

    return count

async def main():
    await db_manager.connect()
    try:
        saved_count = await search_and_collect_top_20_videos()
        logger.info(f"🏁 Completed. Saved {saved_count} new videos.")
    except Exception as e:
        logger.exception(f"Fatal error in main: {e}")
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    # Fix for Windows asyncio loop policy if needed
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())