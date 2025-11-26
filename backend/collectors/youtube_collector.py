"""
YouTube Video Collector - Top 20 Most Viewed from Latest Videos
Strategy: Tìm videos mới -> Fetch metadata -> Tính priority score -> Lấy top 20
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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBagCvsURNXknATznFLl717toi7YJEE76M")
if not GEMINI_API_KEY:
    logger.warning("⚠️ GEMINI_API_KEY not found. Summarization will be skipped.")
else:
    genai.configure(api_key=GEMINI_API_KEY)

gemini_model = genai.GenerativeModel('gemini-2.5-flash')
executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

VINGROUP_KEYWORDS = [
    "vingroup", "phạm nhật vượng", "vinfast", "xe điện vinfast", 
    "vinhomes", "vinpearl", "vinmec", "vf8", "vf9", "vf3","vinspeed",
    "vinbus", "vincom","vinspace"
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

def calculate_priority_score(video: Dict, reference_date: datetime) -> Tuple[float, int]:
    """
    Tính điểm ưu tiên cho video:
    - Video trong 30 ngày: Điểm cao (dựa vào view count)
    - Video > 30 ngày: Bị phạt MẠNH (giảm điểm theo cấp số nhân)
    
    Công thức:
    - Nếu <= 30 ngày: score = view_count × (1.0 ~ 2.0) [bonus theo độ mới]
    - Nếu > 30 ngày: score = view_count × penalty_factor [giảm mạnh]
    
    Returns:
        Tuple[float, int]: (Điểm ưu tiên, Số ngày tuổi)
    """
    view_count = video.get('view_count', 0) or 0
    upload_date = video.get('upload_date')
    timestamp = video.get('timestamp')
    
    # Parse upload date - ưu tiên timestamp trước
    upload_datetime = None
    
    # Thử parse từ timestamp trước
    if timestamp:
        try:
            if isinstance(timestamp, (int, float)):
                upload_datetime = datetime.fromtimestamp(timestamp)
            elif isinstance(timestamp, str):
                upload_datetime = datetime.fromtimestamp(int(timestamp))
        except:
            pass
    
    # Nếu không có timestamp, dùng upload_date
    if not upload_datetime and upload_date:
        if isinstance(upload_date, str) and upload_date != 'N/A':
            try:
                upload_datetime = datetime.strptime(upload_date, '%Y%m%d')
            except:
                pass
    
    # Nếu vẫn không có, coi như video cũ (60 ngày)
    if not upload_datetime:
        upload_datetime = reference_date - timedelta(days=60)
    
    # Tính số ngày kể từ khi upload
    days_old = (reference_date - upload_datetime).days
    if days_old < 0:
        days_old = 0
    
    # === CÔNG THỨC ƯU TIÊN ===
    
    if days_old <= 30:
        # Video trong 30 ngày: Được ưu tiên cao
        # Bonus tăng dần cho video mới hơn
        # 0-7 ngày: bonus 2.0x
        # 8-14 ngày: bonus 1.7x
        # 15-21 ngày: bonus 1.4x
        # 22-30 ngày: bonus 1.2x
        
        if days_old <= 7:
            recency_bonus = 2.0
        elif days_old <= 14:
            recency_bonus = 1.7
        elif days_old <= 21:
            recency_bonus = 1.4
        else:  # 22-30 ngày
            recency_bonus = 1.2
        
        score = view_count * recency_bonus
        
    else:
        # Video > 30 ngày: Bị phạt MẠNH
        # Công thức penalty: 0.5 ^ ((days_old - 30) / 30)
        # 31-60 ngày: giảm còn 50% -> 25%
        # 61-90 ngày: giảm còn 25% -> 12.5%
        # 91+ ngày: giảm còn < 10%
        
        extra_days = days_old - 30
        penalty_factor = 0.5 ** (extra_days / 30)
        
        # Đảm bảo penalty không quá nhỏ (tối thiểu 1%)
        penalty_factor = max(penalty_factor, 0.01)
        
        score = view_count * penalty_factor
    
    return score, days_old

# ==============================================================================
# 2. CORE LOGIC
# ==============================================================================

async def get_video_details_and_save(db_ops, url, analyzer, video_metadata=None):
    """
    Lấy chi tiết video và lưu vào database
    
    Args:
        db_ops: Database operations object
        url: Video URL
        analyzer: Sentiment analyzer
        video_metadata: Metadata từ search (có thể có upload_date)
    """
    loop = asyncio.get_running_loop()
    
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'skip_download': True,
        'getcomments': True,
        'ignoreerrors': True,
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
    
    # Merge metadata từ search nếu có (để giữ upload_date)
    if video_metadata:
        if not info.get('upload_date') and video_metadata.get('upload_date'):
            info['upload_date'] = video_metadata.get('upload_date')
        if not info.get('timestamp') and video_metadata.get('timestamp'):
            info['timestamp'] = video_metadata.get('timestamp')
    
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
        "published_at": _convert_timestamp(info.get('upload_date') or info.get('timestamp')),
        "collected_at": datetime.now(),
        "language": "vi",
        "is_processed": True
    }

    post_id = await db_ops.insert_post(post_data)
    if not post_id: return False

    # 5. Xử lý Comment
    raw_comments = info.get('comments') or [] 
    
    if raw_comments:
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
        logger.info(f"✅ Saved: {post_data['title'][:50]}... (V:{post_data['views_count']:,}, C:{saved_comments})")
    else:
        logger.info(f"✅ Saved: {post_data['title'][:50]}... (Views: {post_data['views_count']:,}, Comments disabled/empty)")
        
    return True

async def search_and_collect_top_20_videos():
    """
    CHIẾN LƯỢC MỚI:
    1. Tìm 500 video URLs (search flat)
    2. Fetch metadata (upload_date) cho mỗi video
    3. Tính điểm ưu tiên (ưu tiên video trong 30 ngày)
    4. Lấy top 20 video có điểm cao nhất
    5. Lưu và phân tích đầy đủ 20 video đó
    """
    db_ops = DatabaseOperations()
    analyzer = VietnameseSentimentAnalyzer()
    
    now = datetime.now()
    days_ago_30 = now - timedelta(days=30)
    date_str = days_ago_30.strftime('%Y%m%d')
    
    query = " | ".join(VINGROUP_KEYWORDS[:5])
    logger.info(f"🚀 Searching latest videos since {date_str}...")
    
    # BƯỚC 1: Search để lấy danh sách video URLs
    ydl_search_opts = {
        'quiet': True,
        'extract_flat': True,  # Chỉ lấy URLs thôi
        'skip_download': True,
        'ignoreerrors': True,
    }
    
    loop = asyncio.get_running_loop()
    found_entries = []
    
    try:
        def run_search():
            with YoutubeDL(ydl_search_opts) as ydl:
                # Tìm nhiều video hơn để có đủ sau khi filter
                return ydl.extract_info(f"ytsearch500:{query}", download=False)
        
        info = await loop.run_in_executor(executor, run_search)
        
        if 'entries' in info:
            found_entries = [e for e in info['entries'] if e and e.get('id')]
            logger.info(f"📊 Found {len(found_entries)} video URLs")
    except Exception as e:
        logger.error(f"Search error: {e}")
        return 0

    if not found_entries:
        logger.warning("⚠️ No videos found!")
        return 0
    
    # BƯỚC 2: Fetch metadata nhẹ cho mỗi video để lấy upload_date
    logger.info(f"📥 Fetching metadata for {len(found_entries)} videos (this may take a while)...")
    
    async def fetch_video_metadata(video_entry):
        """Fetch minimal metadata để lấy upload_date và view_count"""
        try:
            url = video_entry.get('url') or f"https://www.youtube.com/watch?v={video_entry.get('id')}"
            
            def get_info():
                with YoutubeDL({'quiet': True, 'skip_download': True, 'no_warnings': True}) as ydl:
                    return ydl.extract_info(url, download=False)
            
            video_info = await loop.run_in_executor(executor, get_info)
            
            if video_info:
                return {
                    'id': video_info.get('id'),
                    'url': url,
                    'title': video_info.get('title'),
                    'view_count': video_info.get('view_count', 0),
                    'upload_date': video_info.get('upload_date'),
                    'timestamp': video_info.get('timestamp'),
                }
        except Exception as e:
            logger.debug(f"Failed to fetch metadata for {video_entry.get('id')}: {e}")
            return None
    
    # Fetch metadata song song (batch processing)
    batch_size = 10
    videos_with_metadata = []
    
    for i in range(0, len(found_entries), batch_size):
        batch = found_entries[i:i+batch_size]
        tasks = [fetch_video_metadata(vid) for vid in batch]
        results = await asyncio.gather(*tasks)
        videos_with_metadata.extend([r for r in results if r and r.get('view_count')])
        
        logger.info(f"  Progress: {min(i+batch_size, len(found_entries))}/{len(found_entries)} videos processed")
        await asyncio.sleep(1)  # Rate limiting
    
    logger.info(f"✅ Successfully fetched metadata for {len(videos_with_metadata)} videos")
    
    if not videos_with_metadata:
        logger.warning("⚠️ No valid video metadata found!")
        return 0
    
    # BƯỚC 3: Tính điểm ưu tiên cho mỗi video
    logger.info(f"🧮 Calculating priority scores (30-day preference)...")
    for vid in videos_with_metadata:
        score, days = calculate_priority_score(vid, now)
        vid['priority_score'] = score
        vid['days_old'] = days
    
    # BƯỚC 4: Sắp xếp theo điểm ưu tiên và lấy top 20
    videos_with_metadata.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
    top_20_videos = videos_with_metadata[:20]
    
    # BƯỚC 5: Hiển thị kết quả
    logger.info(f"🎯 Top 20 videos by priority score (30-day preference):")
    for i, vid in enumerate(top_20_videos[:10], 1):
        views = vid.get('view_count', 0)
        score = vid.get('priority_score', 0)
        days_old = vid.get('days_old', -1)
        title = vid.get('title', 'N/A')[:60]
        
        # Hiển thị status dựa trên tuổi video
        if days_old <= 7:
            status = "🔥 NEW"
        elif days_old <= 30:
            status = "✅ RECENT"
        elif days_old <= 60:
            status = "⚠️ OLD"
        else:
            status = "❌ VERY OLD"
        
        logger.info(f"  {i}. {title}")
        logger.info(f"     {status} | Views: {views:,} | Age: {days_old}d | Score: {score:,.0f}")

    # BƯỚC 6: Lưu 20 video vào database
    count = 0
    for vid in top_20_videos:
        url = vid.get('url')
        if not url:
            continue
            
        if await db_ops.get_post_by_url(url):
            logger.info(f"⏭️  Skipping existing: {url}")
            continue
            
        try:
            # Pass metadata từ search để giữ thông tin upload_date
            success = await get_video_details_and_save(db_ops, url, analyzer, video_metadata=vid)
            if success:
                count += 1
                await asyncio.sleep(2)  # Tránh rate limit
        except Exception as e:
            logger.error(f"❌ Error processing video {url}: {e}")
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
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())