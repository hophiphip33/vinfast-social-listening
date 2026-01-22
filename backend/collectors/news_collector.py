"""
News Collector - Optimized Version
Features: Google News RSS + Concurrency + Robust Date Parsing + Safe Timezone
"""

import os
import sys
import asyncio
import json
import concurrent.futures
import random
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import List, Dict
import re

# Thư viện ngoài
import feedparser
from dateutil import parser as date_parser
from newspaper import Article, Config
from loguru import logger
import google.generativeai as genai

# --- FIX IMPORT ---
# Đảm bảo Python tìm thấy module backend dù chạy từ đâu
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "../../"))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from backend.database.connection import DatabaseOperations, db_manager 
from backend.config.settings import settings
from backend.processors.custom_ai import CustomSentimentModel
from backend.processors.data_processor import data_processor 

# --- CONFIG ---
gemini_model = None
executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

# Khởi tạo Sentiment Model MỘT LẦN DUY NHẤT để tiết kiệm RAM
try:
    GLOBAL_SENTIMENT_MODEL = CustomSentimentModel()
except Exception:
    GLOBAL_SENTIMENT_MODEL = None

# --- INIT GEMINI ---
def init_default_gemini():
    global gemini_model
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY and hasattr(settings, 'GEMINI_API_KEYS') and settings.GEMINI_API_KEYS:
        GEMINI_API_KEY = settings.GEMINI_API_KEYS[0]
    
    if GEMINI_API_KEY:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            logger.error(f"Gemini Init Error: {e}")

init_default_gemini()

# --- STATIC SOURCES ---
RSS_SOURCES = [
    {"name": "VnExpress - Kinh Doanh", "rss_url": "https://vnexpress.net/rss/kinh-doanh.rss", "category": "Kinh Doanh"},
    {"name": "VnExpress - Xe", "rss_url": "https://vnexpress.net/rss/oto-xe-may.rss", "category": "Xe"},
    {"name": "Dân Trí - Kinh Doanh", "rss_url": "https://dantri.com.vn/kinh-doanh.rss", "category": "Kinh Doanh"},
    {"name": "CafeF", "rss_url": "https://cafef.vn/tai-chinh-kinh-doanh.rss", "category": "Tài chính"},
    {"name": "Thanh Niên - Tài Chính", "rss_url": "https://thanhnien.vn/rss/tai-chinh-kinh-doanh.rss", "category": "Kinh Doanh"}
]

# ==============================================================================
# 1. HELPER: DYNAMIC SOURCES & FILTER
# ==============================================================================

def get_dynamic_sources(keywords: List[str]):
    """Tạo nguồn tin động từ Google News dựa trên từ khóa"""
    sources = list(RSS_SOURCES)
    if keywords:
        # Query: ("VinFast" OR "VF8") when:3d (lấy tin trong 3 ngày)
        # Sử dụng quote_plus để mã hóa URL an toàn
        query = " OR ".join([f'"{k}"' for k in keywords])
        encoded_query = urllib.parse.quote(query)
        
        # hl=vi: ngôn ngữ Việt, gl=VN: khu vực VN, ceid=VN:vi
        google_rss = f"https://news.google.com/rss/search?q={encoded_query}+when:3d&hl=vi&gl=VN&ceid=VN:vi"
        
        sources.append({
            "name": "Google News Aggregator",
            "rss_url": google_rss,
            "category": "Aggregator"
        })
    return sources

def is_relevant_article(title, summary, keywords, brand_name, blacklist):
    """
    Bộ lọc bài viết: Blacklist -> Brand -> Keywords
    """
    text = f"{title} {summary}".lower()
    
    # 1. Check Blacklist (Critical)
    if blacklist:
        for bad_word in blacklist:
            if bad_word.lower() in text: return False
    
    # 2. Check Brand (Ưu tiên cao)
    if brand_name and brand_name.lower() in text: return True

    # 3. Check Keywords
    if keywords:
        for kw in keywords:
            # Regex check boundary: \bword\b để tránh match nhầm
            # re.IGNORECASE để không phân biệt hoa thường
            if re.search(r'\b' + re.escape(kw) + r'\b', text, re.IGNORECASE):
                return True
            if kw.lower() in text: # Fallback simple check
                return True
            
    return False

# ==============================================================================
# 2. FETCHING LOGIC
# ==============================================================================

def fetch_rss_articles_sync(source, keywords, brand_name, blacklist):
    try:
        # Thêm User-Agent để tránh bị chặn bởi một số RSS Server
        feed = feedparser.parse(source['rss_url'], agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        
        if not feed.entries: return []
        
        filtered = []
        now = datetime.now()
        
        for entry in feed.entries:
            title = entry.get('title', '')
            summary = entry.get('summary', '')
            link = entry.get('link', '')
            
            # Lọc nội dung
            if not is_relevant_article(title, summary, keywords, brand_name, blacklist):
                continue
            
            # --- XỬ LÝ NGÀY THÁNG (QUAN TRỌNG) ---
            pub_date = now
            date_str = entry.get('published') or entry.get('updated') or entry.get('created')
            
            if date_str:
                try:
                    # Parse ngày tháng
                    dt = date_parser.parse(date_str)
                    
                    # Chuyển đổi về navie datetime (bỏ múi giờ) để thống nhất so sánh
                    if dt.tzinfo:
                        pub_date = dt.astimezone(timezone.utc).replace(tzinfo=None)
                    else:
                        pub_date = dt
                except: 
                    pass
            
            # Chỉ lấy tin trong 3 ngày đổ lại
            if (now - pub_date).days <= 3:
                filtered.append({
                    'title': title, 
                    'link': link, 
                    'summary': summary,
                    'published_date': pub_date, 
                    'source_name': source['name'],
                    'category': source['category']
                })
        return filtered
    except Exception as e:
        logger.error(f"RSS Error {source['name']}: {e}")
        return []

async def fetch_rss_articles(source, keywords, brand_name, blacklist):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, fetch_rss_articles_sync, source, keywords, brand_name, blacklist)

def fetch_full_article_sync(url):
    """
    Dùng Newspaper3k để tải nội dung chi tiết bài báo
    """
    try:
        config = Config()
        config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        config.request_timeout = 10
        
        article = Article(url, config=config)
        article.download()
        article.parse()
        
        # Bỏ qua nếu bài quá ngắn (có thể là lỗi parse hoặc paywall)
        if not article.text or len(article.text) < 100: return None
        
        return {
            "title": article.title, 
            "text": article.text,
            "top_image": article.top_image, 
            "authors": article.authors,
            "publish_date": article.publish_date
        }
    except: return None

async def fetch_article_content(url):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, fetch_full_article_sync, url)

# ==============================================================================
# 3. ANALYSIS & SAVING
# ==============================================================================

async def gemini_analyze_news(text, brand_name):
    """Gọi Gemini để phân tích nội dung"""
    if not gemini_model: return {}
    loop = asyncio.get_running_loop()
    
    def _call():
        try:
            prompt = f"""
            Bạn là chuyên gia phân tích truyền thông. Hãy phân tích bài viết dưới đây về thương hiệu "{brand_name}".
            
            Trả về kết quả dưới dạng JSON hợp lệ (không Markdown) với cấu trúc sau:
            {{
                "summary": "Tóm tắt ngắn gọn 3 câu chính, tập trung vào tác động tới thương hiệu.",
                "risk_analysis": "Đánh giá là: TÍCH CỰC, TIÊU CỰC, hay TRUNG TÍNH.",
                "key_topics": ["Chủ đề 1", "Chủ đề 2"],
                "sentiment_explanation": "Giải thích ngắn gọn tại sao lại đánh giá như vậy."
            }}
            
            Nội dung bài viết:
            {text[:15000]}
            """
            res = gemini_model.generate_content(prompt)
            # Làm sạch chuỗi JSON nếu Gemini trả về markdown
            clean_text = res.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except Exception as e: 
            return {}

    return await loop.run_in_executor(executor, _call)

async def process_and_save_article(db_ops, article_meta, sentiment_model, brand_name):
    url = article_meta['link']
    
    # 1. Check duplicate nhanh (tránh tốn AI token)
    if await db_ops.get_post_by_url(url): return False
    
    # 2. Fetch Content
    content = await fetch_article_content(url)
    if not content: return False
    
    full_text = content['text']
    title = content['title'] or article_meta['title']
    
    # 3. Parallel Analysis (AI + Sentiment)
    ai_data = await gemini_analyze_news(f"{title}\n{full_text}", brand_name)
    
    # 4. Scoring Logic
    # Sentiment Model trả về từ -1 đến 1
    sentiment_score = 0
    if sentiment_model:
        sentiment_score = sentiment_model.predict(f"{title}. {full_text[:1000]}")
    
    # AI Risk Analysis -> Score
    risk_text = ai_data.get('risk_analysis', '').lower()
    ai_score_val = 0.8 if 'tích cực' in risk_text or 'positive' in risk_text else \
                   -0.8 if 'tiêu cực' in risk_text or 'negative' in risk_text else 0.0
    
    # Weighted Average: 60% Model NLP + 40% Gemini AI
    final_score = (0.6 * sentiment_score) + (0.4 * ai_score_val)
    
    # Labeling
    sentiment_label = "NEUTRAL"
    if final_score > 0.15: sentiment_label = "POSITIVE"
    if final_score < -0.15: sentiment_label = "NEGATIVE"

    # Tính Marketing Score (Thang 10)
    # final_score (-1 -> 1) => Marketing Score (0 -> 10)
    # Công thức sigmoid-like đơn giản
    marketing_score = round(min(10, max(0, (final_score + 1) * 5)), 1)

    # 5. Save to DB
    doc = {
        "platform": "news",
        "source_url": url,
        "source_name": article_meta['source_name'],
        "title": title,
        # Ưu tiên tóm tắt của AI, nếu lỗi thì cắt text
        "content": ai_data.get('summary') or full_text[:300] + "...",
        "full_text": full_text[:5000], # Lưu tối đa 5000 ký tự để tiết kiệm DB
        "thumbnail_url": content['top_image'],
        "published_at": content['publish_date'] or article_meta['published_date'],
        "collected_at": datetime.now(),
        
        "sentiment": sentiment_label,
        "sentiment_score": round(final_score, 3),
        "marketing_score": marketing_score,
        
        "brand_name": brand_name,
        "keywords": data_processor.extract_keywords(full_text)[:5] if data_processor else [],
        "extra_data": {
            "topics": ai_data.get('key_topics', []),
            "ai_explanation": ai_data.get('sentiment_explanation', '')
        },
        # Các trường mặc định cho thống kê
        "views_count": 0,
        "likes_count": 0,
        "comments_count": 0,
        "shares_count": 0,
        "is_processed": True
    }
    
    await db_ops.insert_post(doc)
    logger.info(f"📰 Saved: {title[:30]}... [{sentiment_label} - {marketing_score}]")
    return True

# ==============================================================================
# 4. MAIN ORCHESTRATOR
# ==============================================================================

async def search_and_collect_news(keywords, brand_name, blacklist=[], api_keys=[]):
    if not keywords: return 0
    
    # 1. Config Dynamic Key (Cấu hình lại Gemini nếu có key mới)
    global gemini_model
    if api_keys:
        try:
            # Random key để load balancing
            key = random.choice(api_keys)
            genai.configure(api_key=key)
            gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        except: 
            pass # Giữ nguyên model cũ nếu lỗi cấu hình

    db_ops = DatabaseOperations()
    
    # Sử dụng Global Sentiment Model để tránh load lại nặng RAM
    sentiment_model = GLOBAL_SENTIMENT_MODEL or CustomSentimentModel()

    # 2. Gather URLs from RSS (Bao gồm Google News)
    sources = get_dynamic_sources(keywords)
    logger.info(f"📡 Scanning {len(sources)} sources for '{brand_name}'...")
    
    rss_tasks = [fetch_rss_articles(s, keywords, brand_name, blacklist) for s in sources]
    results = await asyncio.gather(*rss_tasks)
    
    # 3. Flatten & Deduplicate
    articles = [item for sublist in results for item in sublist]
    
    # Deduplicate by Link (Dùng Dict comprehension)
    unique_articles_map = {a['link']: a for a in articles}
    unique_articles = list(unique_articles_map.values())
    
    # Sort by Date (Mới nhất trước) & Limit
    sorted_articles = sorted(unique_articles, key=lambda x: x['published_date'], reverse=True)[:30]
    
    logger.info(f"🔍 Processing {len(sorted_articles)} potential articles (from {len(unique_articles)} raw)...")

    # 4. Process in Parallel (Max 5 concurrent để tránh rate limit)
    sem = asyncio.Semaphore(5)
    
    async def _worker(art):
        async with sem:
            try:
                return await process_and_save_article(db_ops, art, sentiment_model, brand_name)
            except Exception as e:
                logger.warning(f"Failed processing {art['link']}: {e}")
                return False

    save_tasks = [_worker(a) for a in sorted_articles]
    results = await asyncio.gather(*save_tasks)
    
    total = sum(1 for r in results if r)
    if total > 0:
        logger.success(f"✅ Finished News Collection. Saved {total} new articles for {brand_name}.")
    else:
        logger.info(f"💤 News Collection finished. No new valid articles found for {brand_name}.")
        
    return total

if __name__ == "__main__":
    # Test Block
    async def main():
        await db_manager.connect()
        try:
            await search_and_collect_news(
                keywords=["VinFast", "Vingroup", "VF3"], 
                brand_name="VinFast",
                blacklist=["xổ số", "bóng đá", "tệ nạn"],
                api_keys=[]
            )
        finally:
            await db_manager.disconnect()

    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())