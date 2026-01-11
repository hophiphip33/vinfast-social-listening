"""
YouTube Video Collector - Dynamic Version
- Target: Top 100 videos (30 days window) based on User Keywords
- Comments: Top 30 per video
- Performance: Optimized with ThreadPoolExecutor
"""

import os
import sys
import asyncio
import requests
import concurrent.futures
import math
import random  # [MỚI] Thêm thư viện random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

# --- 1. FIX LỖI IMPORT ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "../../"))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# --- IMPORT MODULES ---
from backend.database.connection import DatabaseOperations, db_manager 
from backend.config.settings import settings
from backend.processors.custom_ai import CustomSentimentModel 

from yt_dlp import YoutubeDL
from loguru import logger
import google.generativeai as genai

# --- CẤU HÌNH GEMINI (MẶC ĐỊNH) ---
# Biến global để lưu model hiện tại
gemini_model = None

# Hàm khởi tạo Gemini mặc định (nếu không có key động)
def init_default_gemini():
    global gemini_model
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        if hasattr(settings, 'GEMINI_API_KEYS') and settings.GEMINI_API_KEYS:
            GEMINI_API_KEY = settings.GEMINI_API_KEYS[0]
    
    if GEMINI_API_KEY:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            gemini_model = genai.GenerativeModel('gemini-2.5-flash')
        except Exception as e:
            logger.error(f"Lỗi cấu hình Gemini mặc định: {e}")

# Gọi khởi tạo lần đầu
init_default_gemini()

# Tối ưu hóa luồng xử lý
executor = concurrent.futures.ThreadPoolExecutor(max_workers=6)

# ==============================================================================
# 2. CÁC HÀM HỖ TRỢ
# ==============================================================================

def gemini_summarize_sync(text, brand_name, max_words=500):
    """
    Tóm tắt nội dung video, tập trung vào Brand Name
    """
    if not text or not gemini_model: return None
    try:
        text = text[:10000] # Giới hạn input
        
        # Prompt động theo Brand Name
        prompt = f"""Hãy tóm tắt nội dung sau đây thành khoảng {max_words} từ. 
Tập trung vào những điểm chính và thông tin quan trọng nhất liên quan đến thương hiệu "{brand_name}".
Trả lời bằng Tiếng Việt.

Nội dung:
{text}

Tóm tắt:"""
        
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"⚠️ Gemini summarization failed: {e}")
        return None

async def gemini_summarize(text, brand_name, max_words=500):
    loop = asyncio.get_running_loop()
    if not gemini_model: return ""
    await asyncio.sleep(5) # Rate limiting nhẹ
    return await loop.run_in_executor(executor, gemini_summarize_sync, text, brand_name, max_words)

def get_dislikes_sync(video_id):
    try:
        url = f"https://returnyoutubedislikeapi.com/votes?videoId={video_id}"
        resp = requests.get(url, timeout=3)
        if resp.status_code == 200:
            return resp.json().get("dislikes", 0)
    except:
        pass
    return 0

async def get_dislikes(video_id):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, get_dislikes_sync, video_id)

def get_transcript_sync(video_id):
    """
    Lấy phụ đề YouTube (bao gồm cả tự động)
    """
    try:
        # Phương pháp 1: Sử dụng list_transcripts (phiên bản mới >= 0.5.0)
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # 1. Thử lấy phụ đề thủ công Tiếng Việt
            try:
                transcript = transcript_list.find_manually_created_transcript(['vi'])
            except:
                # 2. Thử lấy phụ đề tự động Tiếng Việt
                try:
                    transcript = transcript_list.find_generated_transcript(['vi'])
                except:
                    # 3. Thử lấy phụ đề thủ công Tiếng Anh
                    try:
                        transcript = transcript_list.find_manually_created_transcript(['en'])
                    except:
                        # 4. Thử lấy phụ đề tự động Tiếng Anh
                        try:
                            transcript = transcript_list.find_generated_transcript(['en'])
                        except:
                            # 5. Lấy bất kỳ phụ đề nào
                            try:
                                manual = [t for t in transcript_list if not t.is_generated]
                                if manual: transcript = manual[0]
                                else:
                                    generated = [t for t in transcript_list if t.is_generated]
                                    if generated: transcript = generated[0]
                                    else: return "", ""
                            except: return "", ""

            # Dịch sang Tiếng Việt nếu không phải Tiếng Việt
            if transcript.language_code not in ['vi', 'vi-VN']:
                try:
                    transcript = transcript.translate('vi')
                except Exception:
                    pass

            # Lấy nội dung phụ đề
            full_text = " ".join([t['text'] for t in transcript.fetch()])
            transcript_type = "auto-generated" if transcript.is_generated else "manual"
            return full_text, transcript_type
            
        except AttributeError:
            # Phương pháp 2: Fallback cho phiên bản cũ
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['vi', 'en'])
                full_text = " ".join([t['text'] for t in transcript])
                return full_text, "available"
            except:
                return "", ""

    except (TranscriptsDisabled, NoTranscriptFound):
        return "", ""
    except Exception as e:
        logger.error(f"💥 Video {video_id}: Lỗi transcript: {e}")
        return "", ""

async def get_transcript(video_id):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, get_transcript_sync, video_id)

def _convert_timestamp(ts: Any) -> datetime:
    if isinstance(ts, (int, float)): return datetime.fromtimestamp(ts)
    if isinstance(ts, str):
        try: return datetime.strptime(ts, '%Y%m%d')
        except: pass
    return datetime.now()

def calculate_priority_score(video: Dict, reference_date: datetime) -> Tuple[float, int]:
    """Tính điểm ưu tiên để lọc video"""
    view = video.get('view_count', 0) or 0
    u_date = video.get('upload_date')
    
    u_time = None
    if u_date and isinstance(u_date, str):
         try: u_time = datetime.strptime(u_date, '%Y%m%d')
         except: pass
    if not u_time: u_time = reference_date - timedelta(days=60)
    
    days = (reference_date - u_time).days
    if days < 0: days = 0
    
    # Ưu tiên video trong 30 ngày gần nhất
    score = view * (1.5 if days <= 30 else 0.1)
    return score, days

# ==============================================================================
# 3. CORE LOGIC
# ==============================================================================

async def get_video_details_and_save(db_ops, url, sentiment_model, brand_name, video_metadata=None):
    loop = asyncio.get_running_loop()
    
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'skip_download': True,
        'getcomments': True,
        'ignoreerrors': True,
        'extractor_args': {'youtube': {'max_comments': ['50'], 'comment_sort': ['top']}},
    }

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
    
    if video_metadata:
        if not info.get('upload_date') and video_metadata.get('upload_date'):
            info['upload_date'] = video_metadata.get('upload_date')

    # Xử lý nội dung & AI
    transcript_text, _ = await get_transcript(video_id)
    summary = ""
    if transcript_text:
        summary = await gemini_summarize(transcript_text, brand_name, max_words=300)
    elif info.get('description'):
        summary = await gemini_summarize(info.get('description'), brand_name, max_words=200)

    full_content = f"{info.get('title', '')} . {info.get('description', '')}"
    video_sentiment_score = sentiment_model.predict(full_content)
    
    sentiment_label = "NEUTRAL"
    if video_sentiment_score > 0.15: sentiment_label = "POSITIVE"
    elif video_sentiment_score < -0.15: sentiment_label = "NEGATIVE"

    dislikes = await get_dislikes(video_id)
    views = info.get("view_count", 0)
    likes = info.get("like_count", 0)
    comments_count = info.get("comment_count", 0)
    
    # Lưu Post sơ bộ
    post_data = {
        "platform": "youtube",
        "source_url": url,
        "source_name": info.get('uploader', 'YouTube'),
        "title": info.get('title', 'No Title'),
        "content": summary if summary else info.get('description', ''),
        "original_transcript": transcript_text[:1000] + "..." if len(transcript_text) > 1000 else transcript_text,
        "views_count": views,
        "likes_count": likes,
        "dislikes_count": dislikes,
        "comments_count": comments_count,
        "published_at": _convert_timestamp(info.get('upload_date')),
        "collected_at": datetime.now(),
        "is_processed": True,
        "ai_sentiment_raw": video_sentiment_score,
        "sentiment_label": sentiment_label,
        "brand_name": brand_name
    }

    post_id = await db_ops.insert_post(post_data)
    if not post_id: return False

    # Xử lý Comment
    raw_comments = info.get('comments') or []
    total_comment_sentiment = 0.0
    processed_count = 0
    target_comments = 30
    
    for c in raw_comments[:target_comments]:
        if not c.get('text'): continue
        try:
            cmt_score = sentiment_model.predict(c['text'])
            cmt_label = "NEUTRAL"
            if cmt_score > 0.15: cmt_label = "POSITIVE"
            elif cmt_score < -0.15: cmt_label = "NEGATIVE"

            await db_ops.insert_comment({
                "post_id": post_id,
                "author": c.get('author'),
                "content": c.get('text'),
                "likes_count": c.get('like_count', 0),
                "published_at": _convert_timestamp(c.get('timestamp')),
                "sentiment": cmt_label,
                "sentiment_score": cmt_score
            })
            total_comment_sentiment += cmt_score
            processed_count += 1
        except: continue
    
    # --- TÍNH TOÁN ĐIỂM SỐ (MARKETING SCORE) ---
    
    # 1. Điểm Cảm xúc Tổng hợp
    if processed_count > 0:
        avg_comment_sentiment = total_comment_sentiment / processed_count
    else:
        avg_comment_sentiment = video_sentiment_score

    total_reactions = likes + dislikes
    reaction_score = 0.0
    if total_reactions > 0:
        reaction_score = (likes - dislikes) / total_reactions
    
    final_sentiment = (video_sentiment_score * 0.3) + (avg_comment_sentiment * 0.5) + (reaction_score * 0.2)

    # 2. View Impact (Log10 ^ 1.3) -> Thưởng lớn cho Video Viral
    if views > 0:
        # Ví dụ: 1M view -> Log=6 -> 6^1.3 = 10.3 điểm
        # 100k view -> Log=5 -> 5^1.3 = 8.1 điểm
        view_factor = math.pow(math.log10(views + 1), 1.3)
    else: 
        view_factor = 0
    
    # Engagement Bonus
    engagement_factor = 1 + ((total_reactions + comments_count * 2) / max(views, 1) * 200)
    raw_impact = view_factor * engagement_factor

    # 3. Time Decay (Cấp số nhân lùi: 0.1 ^ (số tháng))
    pub_date = _convert_timestamp(info.get('upload_date'))
    age_days = (datetime.now() - pub_date).days
    if age_days < 0: age_days = 0
    
    # Công thức: 0.1 mũ (số ngày / 30)
    # - Ngày 0: 0.1^0 = 1 (100%)
    # - Ngày 15: 0.1^0.5 = 0.31 (31%)
    # - Ngày 30: 0.1^1 = 0.1 (10%)
    # - Ngày 60: 0.1^2 = 0.01 (1%)
    time_decay = math.pow(0.1, age_days / 30.0)

    # 4. Marketing Score Final
    # Nhân thêm 2.5 để scale điểm lên trước khi nén sigmoid
    marketing_score = 10 * (1 - math.exp(-(abs(final_sentiment) * raw_impact * time_decay * 2.5) / 25))
    marketing_score = round(marketing_score, 2)

    final_label = "NEUTRAL"
    if final_sentiment > 0.15: final_label = "POSITIVE"
    elif final_sentiment < -0.15: final_label = "NEGATIVE"

    update_data = {
        "crowd_sentiment": round(avg_comment_sentiment, 3),
        "reaction_score": round(reaction_score, 3),
        "sentiment_score": round(final_sentiment, 3),   
        "marketing_score": marketing_score,  
        "sentiment": final_label
    }

    await db_ops.update_post_score(post_id, update_data)

    logger.info(f"✅ Saved: {info.get('title', '')[:20]}... | MktScore: {marketing_score} | ViewImpact: {round(view_factor, 1)} | Decay: {round(time_decay, 3)}")
    return True

async def search_and_collect_videos(keywords: List[str] = None, brand_name: str = None, blacklist: List[str] = [], api_keys: List[str] = []):
    """
    Hàm chính [CẬP NHẬT]:
    - blacklist: Danh sách từ khóa cấm để lọc video.
    - api_keys: Danh sách key API để chọn ngẫu nhiên cho Gemini.
    """
    if not keywords or not brand_name:
        logger.warning("⚠️ Thiếu Keywords hoặc Brand Name. Bỏ qua thu thập YouTube.")
        return 0

    db_ops = DatabaseOperations()
    
    # --- [MỚI] CẤU HÌNH API KEY ĐỘNG ---
    global gemini_model
    if api_keys:
        try:
            # Chọn ngẫu nhiên 1 key trong danh sách
            selected_key = random.choice(api_keys)
            genai.configure(api_key=selected_key)
            gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)
            # logger.info(f"🔑 YoutubeCollector dùng Key: ...{selected_key[-4:]}")
        except Exception as e:
            logger.warning(f"⚠️ Lỗi cấu hình Dynamic Key: {e}. Dùng key mặc định.")

    logger.info("🤖 Loading Custom AI Model...")
    try:
        sentiment_model = CustomSentimentModel()
    except Exception as e:
        logger.error(f"Lỗi load model AI: {e}")
        return 0
    
    now = datetime.now()
    
    # Tạo Query Search từ 5 từ khóa đầu tiên của User
    query = " | ".join(keywords[:5])
    logger.info(f"🚀 Tìm kiếm Video cho Brand: {brand_name} | Query: {query}")
    
    ydl_search_opts = {
        'quiet': True,
        'extract_flat': True, 
        'skip_download': True,
        'ignoreerrors': True,
    }
    
    loop = asyncio.get_running_loop()
    found_entries = []
    
    try:
        def run_search():
            with YoutubeDL(ydl_search_opts) as ydl:
                # Tìm 200 video để có đủ nguồn lọc
                return ydl.extract_info(f"ytsearch200:{query}", download=False)
        
        info = await loop.run_in_executor(executor, run_search)
        if 'entries' in info:
            found_entries = [e for e in info['entries'] if e and e.get('id')]
    except: return 0

    # --- [MỚI] LỌC BLACKLIST ---
    filtered_entries = []
    for vid in found_entries:
        title = vid.get('title', '').lower()
        is_spam = False
        if blacklist:
            for bad_word in blacklist:
                if bad_word in title:
                    is_spam = True
                    break
        if not is_spam:
            filtered_entries.append(vid)

    logger.info(f"📥 Tìm thấy {len(filtered_entries)} video sạch (đã loại {len(found_entries) - len(filtered_entries)} video rác). Đang lấy metadata...")
    
    # Helper fetch metadata
    async def fetch_meta(vid):
        try:
            url = vid.get('url') or f"https://www.youtube.com/watch?v={vid.get('id')}"
            def get():
                with YoutubeDL({'quiet':True, 'skip_download':True}) as ydl:
                    return ydl.extract_info(url, download=False)
            data = await loop.run_in_executor(executor, get)
            if data: return {
                'id': data.get('id'), 'url': url, 'title': data.get('title'),
                'view_count': data.get('view_count', 0), 'upload_date': data.get('upload_date')
            }
        except: return None
        
    videos_with_meta = []
    batch_size = 40
    
    for i in range(0, len(filtered_entries), batch_size):
        batch = filtered_entries[i:i+batch_size]
        res = await asyncio.gather(*[fetch_meta(v) for v in batch])
        videos_with_meta.extend([r for r in res if r])
        await asyncio.sleep(0.1)
        
    # Tính điểm và lọc
    for v in videos_with_meta:
        score, _ = calculate_priority_score(v, now)
        v['priority_score'] = score
        
    videos_with_meta.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
    
    # Lấy Top 50 video chất lượng nhất để xử lý sâu
    top_videos = videos_with_meta[:50]
    
    logger.info(f"🎯 Chọn Top {len(top_videos)} video để phân tích sâu...")
    
    count = 0
    for vid in top_videos:
        if await db_ops.get_post_by_url(vid['url']): 
            continue
        try:
            # Truyền brand_name vào hàm xử lý chi tiết
            success = await get_video_details_and_save(db_ops, vid['url'], sentiment_model, brand_name, vid)
            if success: count += 1
        except: continue
        
    return count

async def main():
    # Test chạy độc lập
    await db_manager.connect()
    try:
        c = await search_and_collect_videos(
            keywords=["VinFast", "VF8"], 
            brand_name="VinFast",
            blacklist=["xổ số", "game bài"], # Test blacklist
            api_keys=[] # Test api keys
        )
        logger.info(f"🏁 Hoàn tất. Đã lưu {c} video vào hệ thống.")
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())