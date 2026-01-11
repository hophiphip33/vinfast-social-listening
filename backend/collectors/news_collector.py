"""
News Collector - Dynamic Version
Strategy: RSS Parser -> Dynamic Filter (User Keywords & Brand & Blacklist) -> AI Analysis -> DB Save
"""

import os
import sys
import asyncio
import json
import concurrent.futures
import random  # [MỚI] Thêm thư viện random để chọn API Key
from datetime import datetime, timedelta
from typing import List, Dict
import feedparser

# --- FIX LỖI IMPORT ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "../../"))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# --- IMPORT MODULES ---
from backend.database.connection import DatabaseOperations, db_manager 
from backend.config.settings import settings
from backend.processors.custom_ai import CustomSentimentModel
from backend.processors.data_processor import data_processor 

from newspaper import Article, Config
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

executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

# ==============================================================================
# DANH SÁCH NGUỒN TIN RSS
# ==============================================================================
RSS_SOURCES = [
    {"name": "VnExpress - Kinh Doanh", "rss_url": "https://vnexpress.net/rss/kinh-doanh.rss", "category": "Kinh Doanh"},
    {"name": "VnExpress - Xe", "rss_url": "https://vnexpress.net/rss/oto-xe-may.rss", "category": "Xe"},
    {"name": "Dân Trí - Kinh Doanh", "rss_url": "https://dantri.com.vn/kinh-doanh.rss", "category": "Kinh Doanh"},
    {"name": "Tuổi Trẻ - Kinh Doanh", "rss_url": "https://tuoitre.vn/rss/kinh-doanh.rss", "category": "Kinh Doanh"},
    {"name": "Thanh Niên - Kinh Doanh", "rss_url": "https://thanhnien.vn/rss/kinh-doanh.rss", "category": "Kinh Doanh"},
    {"name": "CafeF", "rss_url": "https://cafef.vn/tai-chinh-kinh-doanh.rss", "category": "Tài chính"}
]

# ==============================================================================
# 1. RSS PARSER & DYNAMIC FILTER
# ==============================================================================

def is_relevant_article(title, summary, keywords: List[str], brand_name: str, blacklist: List[str] = []):
    """
    Kiểm tra bài báo có liên quan không.
    [CẬP NHẬT] Thêm logic kiểm tra Blacklist.
    """
    import re
    
    # Gộp title và summary để check
    text = f"{title} {summary}".lower()
    
    # 0. [MỚI] Check Blacklist (Ưu tiên cao nhất - Loại bỏ rác)
    if blacklist:
        for bad_word in blacklist:
            # Nếu từ khóa chặn xuất hiện -> Loại ngay
            if bad_word in text:
                return False
    
    # 1. Remove URLs
    text = re.sub(r'http\S+|www\S+', '', text)
    
    # 2. Check Brand Name (Ưu tiên tiếp theo)
    if brand_name and brand_name.lower() in text:
        return True

    # 3. Check Keywords (Dynamic)
    if keywords:
        for keyword in keywords:
            # Dùng word boundary (\b) để khớp chính xác từ
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, text):
                return True
            
            # Fallback
            if " " in keyword:
                if keyword.lower() in text:
                    return True
    
    return False

def fetch_rss_articles_sync(source, keywords, brand_name, blacklist):
    """
    Parse RSS feed và filter theo keywords + brand_name + blacklist
    """
    if not keywords and not brand_name:
        return []

    try:
        feed = feedparser.parse(source['rss_url'])
        if not feed.entries:
            return []
        
        filtered_articles = []
        
        for entry in feed.entries:
            title = entry.get('title', '')
            summary = entry.get('summary', '')
            link = entry.get('link', '')
            
            # --- LOGIC LỌC ĐỘNG (Đã update thêm blacklist) ---
            if not is_relevant_article(title, summary, keywords, brand_name, blacklist):
                continue
            
            # Parse date
            pub_date = datetime.now()
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    pub_date = datetime(*entry.published_parsed[:6])
                except:
                    pass
            
            # Chỉ lấy bài trong 7 ngày
            if (datetime.now() - pub_date).days <= 7:
                filtered_articles.append({
                    'title': title,
                    'link': link,
                    'summary': summary,
                    'published_date': pub_date,
                    'source_name': source['name'],
                    'category': source['category'],
                    'matched_brand': brand_name
                })
        
        return filtered_articles
        
    except Exception as e:
        logger.error(f"❌ Error RSS {source['name']}: {e}")
        return []

async def fetch_rss_articles(source, keywords, brand_name, blacklist):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, fetch_rss_articles_sync, source, keywords, brand_name, blacklist)

# ==============================================================================
# 2. NEWSPAPER3K PARSER
# ==============================================================================

def fetch_full_article_sync(url):
    try:
        config = Config()
        config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        config.request_timeout = 15
        config.fetch_images = False
        config.memoize_articles = False

        article = Article(url, config=config)
        article.download()
        article.parse()
        
        if not article.text or len(article.text) < 200:
            return None
            
        return {
            "title": article.title or "No Title",
            "text": article.text,
            "publish_date": article.publish_date,
            "top_image": article.top_image,
            "authors": article.authors
        }
    except Exception as e:
        return None

async def fetch_article_content(url):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, fetch_full_article_sync, url)

# ==============================================================================
# 3. GEMINI AI ANALYSIS
# ==============================================================================

def gemini_analyze_news_sync(text, brand_name=""):
    if not text or not gemini_model: return {"summary": None}
    
    try:
        text_input = text[:30000] 
        prompt = f"""
Phân tích bài báo sau liên quan đến thương hiệu "{brand_name}".
Trả về JSON (KHÔNG markdown):
{{
    "summary": "<Tóm tắt 3-4 câu>",
    "risk_analysis": "<Tích cực/Tiêu cực/Trung tính>",
    "key_topics": ["<Chủ đề 1>", "<Chủ đề 2>"],
    "sentiment_explanation": "<Giải thích ngắn>"
}}
Bài báo:
{text_input}
"""
        response = gemini_model.generate_content(prompt)
        result_text = response.text.strip()
        if result_text.startswith("```"):
            result_text = result_text.strip("`").replace("json", "").strip()
        return json.loads(result_text)
    except Exception:
        return {"summary": None}

def fallback_summarize(text, max_sentences=4):
    import re
    sentences = re.split(r'[.!?]\s+', text)
    valid_sentences = [s.strip() for s in sentences if 20 < len(s) < 200]
    if not valid_sentences: return text[:500]
    return ". ".join(valid_sentences[:max_sentences]) + "."

async def gemini_analyze_news(text, brand_name):
    loop = asyncio.get_running_loop()
    if not gemini_model: return {"summary": None}
    await asyncio.sleep(2)
    return await loop.run_in_executor(executor, gemini_analyze_news_sync, text, brand_name)

# ==============================================================================
# 4. PROCESS & SAVE
# ==============================================================================

async def process_and_save_article(db_ops, article_meta, sentiment_model, brand_name):
    url = article_meta.get('link')
    
    # Check duplicate
    existing = await db_ops.get_post_by_url(url)
    if existing: return False
    
    content_data = await fetch_article_content(url)
    if not content_data: return False
        
    full_text = content_data['text']
    title = content_data['title'] or article_meta.get('title')

    # AI Insights
    ai_insights = await gemini_analyze_news(f"{title}\n\n{full_text}", brand_name)
    
    if ai_insights.get('summary'):
        summary = ai_insights['summary']
        summary_method = "Gemini"
    else:
        summary = fallback_summarize(full_text)
        summary_method = "Extractive"

    # Sentiment Analysis
    content_text = f"{title}. {article_meta.get('summary', '')} {full_text[:2000]}"
    content_score = sentiment_model.predict(content_text)
    
    risk_analysis = ai_insights.get('risk_analysis', '').lower()
    ai_score = 0.7 if 'tích cực' in risk_analysis or 'positive' in risk_analysis else \
               -0.7 if 'tiêu cực' in risk_analysis or 'negative' in risk_analysis else 0.0
    
    # Keyword Score
    keywords_found = data_processor.extract_keywords(full_text)
    
    final_score = max(-1.0, min(1.0, (0.6 * content_score) + (0.3 * ai_score)))
    sentiment_label = "positive" if final_score > 0.15 else "negative" if final_score < -0.15 else "neutral"

    # Prepare Data
    post_data = {
        "platform": "news",
        "source_url": url,
        "source_name": article_meta.get('source_name', 'Unknown'),
        "title": title,
        "thumbnail_url": content_data.get('top_image'),
        "content": summary,
        "full_text": full_text[:5000],
        "author": ', '.join(content_data.get('authors', [])) if content_data.get('authors') else None,
        "views_count": 0, "likes_count": 0, "comments_count": 0,
        "published_at": content_data.get('publish_date') or article_meta.get('published_date') or datetime.now(),
        "collected_at": datetime.now(),
        "is_processed": True,
        "language": "vi",
        "sentiment": sentiment_label,
        "sentiment_score": round(final_score, 3),
        "ai_sentiment_raw": round(content_score, 3),
        "crowd_sentiment": round(ai_score, 3),
        "keywords": keywords_found[:10],
        "brand_name": brand_name, 
        "extra_data": {
            "category": article_meta.get('category'),
            "summary_method": summary_method,
            "marketing_score": round(final_score * 100, 2),
            "topics": ai_insights.get('key_topics', [])
        }
    }

    try:
        await db_ops.insert_post(post_data)
        logger.info(f"💾 Saved: {title[:30]}... | Brand: {brand_name}")
        return True
    except Exception as e:
        logger.error(f"Save error: {e}")
        return False

# ==============================================================================
# 5. MAIN WORKFLOW (UPDATED)
# ==============================================================================

async def search_and_collect_news(keywords: List[str] = None, brand_name: str = None, blacklist: List[str] = [], api_keys: List[str] = []):
    """
    Hàm chính [CẬP NHẬT]:
    - blacklist: Danh sách từ khóa cấm (được truyền từ run_collector)
    - api_keys: Danh sách key API (được truyền từ run_collector)
    """
    if not keywords or not brand_name:
        logger.warning("⚠️ Thiếu Keywords hoặc Brand Name. Bỏ qua thu thập News.")
        return 0

    db_ops = DatabaseOperations()
    
    # --- [MỚI] CẤU HÌNH API KEY ĐỘNG ---
    global gemini_model
    if api_keys:
        try:
            # Chọn ngẫu nhiên 1 key trong danh sách để cân bằng tải
            selected_key = random.choice(api_keys)
            genai.configure(api_key=selected_key)
            gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            logger.warning(f"⚠️ Lỗi cấu hình Dynamic Key: {e}. Dùng key mặc định.")
    
    logger.info("🤖 Loading AI Model...")
    try:
        sentiment_model = CustomSentimentModel()
    except Exception:
        return 0

    total_saved = 0
    all_articles = []
    
    logger.info(f"📡 Quét tin tức cho Brand: {brand_name} | Keywords: {keywords} | Blacklist: {len(blacklist)} từ")
    
    # Truyền blacklist vào các hàm fetch RSS
    tasks = [fetch_rss_articles(source, keywords, brand_name, blacklist) for source in RSS_SOURCES]
    results = await asyncio.gather(*tasks)
    
    for articles in results:
        all_articles.extend(articles)
    
    logger.info(f"✅ Tìm thấy {len(all_articles)} bài viết sạch (đã lọc rác).")
    
    # Deduplicate
    seen_urls = set()
    unique_articles = []
    for article in all_articles:
        if article['link'] not in seen_urls:
            seen_urls.add(article['link'])
            unique_articles.append(article)
    
    # Sort & Limit
    unique_articles.sort(key=lambda x: x['published_date'], reverse=True)
    articles_to_process = unique_articles[:20] # Lấy 20 bài mới nhất mỗi lần chạy
    
    # Process
    for article in articles_to_process:
        try:
            success = await process_and_save_article(db_ops, article, sentiment_model, brand_name)
            if success: total_saved += 1
            await asyncio.sleep(0.5)
        except Exception:
            continue
            
    return total_saved

async def main():
    # Test chạy độc lập
    await db_manager.connect()
    try:
        await search_and_collect_news(
            keywords=["VinFast", "VF8"], 
            brand_name="VinFast",
            blacklist=["xổ số", "game bài"],  # Test blacklist
            api_keys=[] # Test default key
        )
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())