import requests
from yt_dlp import YoutubeDL
from youtube_transcript_api import YouTubeTranscriptApi
from pathlib import Path
import os
import google.generativeai as genai
import sys # Thêm thư viện để kiểm tra Python version

# Configure Gemini API
# Lưu ý: Thay thế "YOUR_API_KEY_HERE" bằng khóa API thực tế của bạn
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyCWBJbGRgfSsHwhYDQSVDeVYP8ToolXTWw")
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

# --- HÀM TÓM TẮT BẰNG GEMINI ---
def gemini_summarize(text, max_words=500):
    """
    Sử dụng Gemini API để tóm tắt văn bản
    """
    if not text:
        return None
    
    try:
        # Giới hạn text đầu vào để tránh lỗi token (10000 ký tự tương đương khoảng 2000-2500 tokens)
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
        print(f"⚠️  Gemini summarization failed: {e}")
        # Fallback: Trả về thông báo lỗi rõ ràng
        return f"[Lỗi Tóm Tắt Gemini: {e}. Nội dung có thể quá dài hoặc API gặp sự cố.]" # <--- Tối ưu

# --- HÀM LẤY DISLIKE (DÙNG API BÊN THỨ BA) ---
def get_dislikes(video_id):
    try:
        url = f"https://returnyoutubedislikeapi.com/votes?videoId={video_id}"
        return requests.get(url, timeout=10).json().get("dislikes", None)
    except:
        return None

# --- HÀM LẤY TRANSCRIPT (PHỤ ĐỀ) ---
def get_transcript(video_id):
    """
    Lấy transcript từ YouTube. Ưu tiên Tiếng Việt, sau đó là dịch sang Tiếng Việt, rồi mới đến ngôn ngữ gốc khác.
    Returns tuple: (transcript_text, language_used, error_message)
    """
    # Ngôn ngữ ưu tiên tìm kiếm
    languages_to_try = ['vi', 'en', 'en-US', 'en-GB'] 
    
    print(f"Attempting to fetch transcript for video: {video_id}")
    
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        
        print("\n📝 Available transcripts:")
        available_langs = [t.language_code for t in transcript_list]
        for t in transcript_list:
            status = "Auto" if t.is_generated else "Manual"
            translatable = " [Translatable]" if t.is_translatable else ""
            print(f"  - {t.language_code}: {status}{translatable}")
        
        # 1. Thử tìm transcript trong ngôn ngữ ưu tiên
        for lang in languages_to_try:
            try:
                print(f"\nTrying to find transcript: {lang}")
                transcript = transcript_list.find_transcript([lang])
                data = transcript.fetch()
                text = " ".join([item.text for item in data])
                print(f"✅ Successfully fetched transcript in {lang}")
                return text, lang, None
            except Exception:
                # print(f"  ❌ Not available")
                continue
        
        # 2. Nếu không có match, thử dịch từ ngôn ngữ khác sang Tiếng Việt ('vi')
        print("\nNo exact language match. Trying translation to Vietnamese (vi)...")
        translation_target = 'vi' # <--- Tối ưu: Ưu tiên dịch sang Tiếng Việt
        
        for t in transcript_list:
            if t.is_translatable and t.language_code not in languages_to_try:
                try:
                    print(f"Trying to translate {t.language_code} -> {translation_target}")
                    translated = t.translate(translation_target)
                    data = translated.fetch()
                    text = " ".join([item.text for item in data])
                    print(f"✅ Successfully translated {t.language_code} to {translation_target}")
                    return text, f"{t.language_code}->{translation_target}", None
                except Exception as e:
                    print(f"  ❌ Translation failed: {e}")
                    continue
                    
        # 3. Fallback: Lấy transcript gốc đầu tiên nếu dịch sang Tiếng Việt thất bại
        print("\nTranslation failed. Using first available original transcript...")
        for t in transcript_list:
            try:
                print(f"Using original language: {t.language_code}")
                data = t.fetch()
                text = " ".join([item.text for item in data])
                print(f"✅ Successfully fetched in {t.language_code}")
                return text, t.language_code, None
            except Exception as e:
                print(f"  ❌ Failed: {e}")
                continue
        
        # Nếu thất bại hoàn toàn
        error_msg = f"Available languages: {', '.join(available_langs)}, but could not fetch any"
        print(f"❌ {error_msg}")
        return None, None, error_msg
            
    except Exception as e:
        error_msg = f"Failed to fetch transcripts: {str(e)}"
        print(f"❌ {error_msg}")
        return None, None, error_msg

# --- HÀM TÓM TẮT MÔ TẢ VIDEO ---
def get_video_description_summary(description, max_words=150): # <--- Tối ưu: Thêm max_words
    """
    Tóm tắt mô tả video nếu transcript không khả dụng
    """
    if not description or len(description) < 50:
        return None
    
    print("📄 Using video description for summary...")
    return gemini_summarize(description, max_words=max_words) # <--- Tối ưu: Dùng max_words

# --- HÀM CHÍNH: LẤY THÔNG TIN VIDEO ---
def get_video_info(video_url, top_comments=20, max_summary_words=200): # <--- Tối ưu: Thêm max_summary_words
    ydl_opts = {
        "skip_download": True,
        "quiet": False,
        "getcomments": True,
        "noplaylist": True,
        "extractor_args": {
            "youtube": {
                "max_comments": [str(top_comments * 5)],
                "comment_sort": ["top"]
            }
        }
    }

    print(f"\n🔍 Fetching video info...")
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
    except Exception as e:
        print(f"❌ Lỗi khi trích xuất thông tin video (yt-dlp): {e}")
        return None

    print(f"📹 Processing video: {info.get('title')}")
    video_id = info["id"]

    print("\n" + "="*60)
    print("FETCHING TRANSCRIPT")
    print("="*60)
    
    transcript, lang_used, error_msg = get_transcript(video_id)
    
    transcript_source = None
    if transcript:
        transcript_source = f"youtube-{lang_used}"
    else:
        print(f"\n⚠️  Transcript fetch failed: {error_msg}")

    print("\n" + "="*60)
    print("GENERATING SUMMARY WITH GEMINI")
    print("="*60)
    
    summary = None
    if transcript:
        print(f"✅ Using transcript from: {transcript_source}")
        print(f"📝 Transcript length: {len(transcript)} characters")
        print("🤖 Generating summary with Gemini AI...")
        summary = gemini_summarize(transcript, max_words=max_summary_words) # <--- Tối ưu: Truyền tham số
    else:
        # Fallback to description if no transcript
        description = info.get("description", "")
        if description:
            print("⚠️  No transcript available. Using video description...")
            summary = get_video_description_summary(description, max_words=max_summary_words) # <--- Tối ưu: Truyền tham số
        else:
            print("❌ No transcript or description available")
            summary = "No content available for summarization"

    print("\n" + "="*60)
    print("PROCESSING COMMENTS")
    print("="*60)
    
    comments = info.get("comments", [])
    comments_sorted = sorted(comments, key=lambda c: c.get("like_count", 0), reverse=True)
    comments_top = comments_sorted[:top_comments]
    print(f"✅ Found {len(comments_top)} top comments")
    
    duration_str = f"{info.get('duration') // 60}m {info.get('duration') % 60}s" if info.get('duration') else "N/A"

    return {
        "video_id": video_id,
        "url": video_url,
        "title": info.get("title"),
        "description": info.get("description"),
        "views": info.get("view_count"),
        "likes": info.get("like_count"),
        "dislikes": get_dislikes(video_id),
        "channel": info.get("uploader"),
        "upload_date": info.get("upload_date"),
        "duration_sec": info.get("duration"),
        "duration_str": duration_str,
        "transcript": transcript,
        "transcript_source": transcript_source,
        "transcript_error": error_msg if not transcript else None,
        "summary": summary,
        "top_comments": [
            {
                "author": c.get("author"),
                "text": c.get("text"),
                "likes": c.get("like_count")
            }
            for c in comments_top
        ]
    }


if __name__ == "__main__":
    if "YOUR_API_KEY_HERE" in GEMINI_API_KEY:
        print("🛑 LỖI CẤU HÌNH: Vui lòng thay 'YOUR_API_KEY_HERE' bằng khóa API Gemini của bạn hoặc thiết lập biến môi trường GEMINI_API_KEY.")
        sys.exit(1)

    # Get and validate video URL
    while True:
        video_url = input("Nhập link video YouTube: ").strip()
        if video_url:
            if "youtube.com" in video_url or "youtu.be" in video_url:
                break
            else:
                print("❌ Link không hợp lệ. Vui lòng nhập link YouTube!")
        else:
            print("❌ Vui lòng nhập link!")
    
    # Get number of comments
    while True:
        try:
            top_comments = int(input("Lấy bao nhiêu comment nhiều like? (VD: 20): "))
            if 0 < top_comments <= 50:
                break
            else:
                print("❌ Số lượng phải > 0 và <= 50")
        except ValueError:
            print("❌ Vui lòng nhập số!")
            
    # Get summary length
    while True:
        try:
            max_summary_words = int(input("Độ dài tóm tắt mong muốn? (VD: 200 từ): "))
            if max_summary_words > 0:
                break
            else:
                print("❌ Số lượng từ phải > 0")
        except ValueError:
            print("❌ Vui lòng nhập số!")

    data = get_video_info(video_url, top_comments=top_comments, max_summary_words=max_summary_words) # <--- Tối ưu: Truyền tham số

    if data is None:
        sys.exit(1)

    print("\n" + "="*60)
    print("📊 VIDEO DATA REPORT")
    print("="*60)
    
    print(f"Title: {data['title']}")
    print(f"Channel: {data['channel']}")
    print(f"URL: {data['url']}")
    print(f"Views: {data['views']:,}")
    print(f"Likes: {data['likes']:,}")
    print(f"Dislikes: {data['dislikes']:,}" if data['dislikes'] else "Dislikes: N/A (API failed)")
    print(f"Duration: {data['duration_str']}")
    print(f"Upload Date: {data['upload_date']}")
    print(f"Transcript Source: {data['transcript_source'] if data['transcript_source'] else 'N/A'}")
    
    print("\n" + "="*60)
    print("📝 CONTENT SUMMARY (GEMINI)")
    print("="*60)
    print(data["summary"])

    print("\n" + "="*60)
    print(f"💬 TOP {len(data['top_comments'])} COMMENTS")
    print("="*60)
    for i, c in enumerate(data["top_comments"], 1):
        print(f"\n{i}. 👍 {c['likes']:,} likes | @{c['author']}")
        print(f"   {c['text'][:300]}{'...' if len(c['text']) > 300 else ''}")