import asyncio
from loguru import logger
from backend.database.connection import db_manager

# --- [FIX IMPORT] Sử dụng hàm đúng từ YouTube Collector mới ---
from backend.collectors.youtube_collector import search_and_collect_videos

# Import News Collector (nếu có)
try:
    from backend.collectors.news_collector import NewsCollector
except ImportError:
    NewsCollector = None

def full_collection_pipeline():
    """
    Hàm này được Scheduler gọi tự động theo chu kỳ (ví dụ 5 tiếng/lần).
    Nó chạy trong một Thread riêng nên cần tạo Event Loop mới.
    """
    logger.info("🚀 Worker bắt đầu chạy Full Pipeline (Tự động quét)...")
    
    try:
        # Chuyển từ môi trường Sync (Thread) sang Async
        asyncio.run(run_async_pipeline())
    except Exception as e:
        logger.error(f"❌ Worker Pipeline gặp lỗi: {e}")

async def run_async_pipeline():
    """Logic chính của việc thu thập dữ liệu"""
    await db_manager.connect()
    try:
        # 1. Lấy cấu hình hệ thống (API Keys, Blacklist...)
        config = await db_manager.database["system_config"].find_one()
        api_keys = config.get("api_keys", []) if config else []
        blacklist = config.get("blacklist_keywords", []) if config else []
        
        # 2. Lấy danh sách tất cả User đang hoạt động
        # (Để biết cần quét từ khóa gì: VinFast, VF3, VF8...)
        users = await db_manager.database["users"].find({"is_active": True}).to_list(length=100)
        
        if not users:
            logger.warning("⚠️ Không có user nào hoạt động. Dừng Pipeline.")
            return

        total_youtube_videos = 0
        
        # 3. Duyệt qua từng User và quét dữ liệu theo từ khóa của họ
        for user in users:
            keywords = user.get("keywords", [])
            brand_name = user.get("brand_name", "VinFast")
            
            if not keywords: continue
            
            logger.info(f"🔍 Đang quét dữ liệu cho User: {user.get('email')} | Brand: {brand_name}")
            
            # --- A. CRAWL YOUTUBE ---
            try:
                # Gọi hàm mới search_and_collect_videos
                count = await search_and_collect_videos(
                    keywords=keywords,
                    brand_name=brand_name,
                    blacklist=blacklist,
                    api_keys=api_keys,
                    user_email=user.get("email")
                )
                total_youtube_videos += count
            except Exception as e:
                logger.error(f"Lỗi Youtube Crawl cho user {user.get('email')}: {e}")

            # --- B. CRAWL NEWS (Nếu có module NewsCollector) ---
            if NewsCollector:
                try:
                    # Logic gọi NewsCollector tương tự (nếu bạn đã implement)
                    # await NewsCollector.run(keywords, brand_name...)
                    pass
                except Exception as e:
                    logger.error(f"Lỗi News Crawl: {e}")

        logger.success(f"🏁 Pipeline hoàn tất. Tổng video mới thu thập: {total_youtube_videos}")
        
    finally:
        # Luôn ngắt kết nối DB khi xong việc để tránh treo kết nối
        await db_manager.disconnect()

# --- [OPTIONAL] Hàm hỗ trợ quét 1 URL cụ thể (Dùng cho API thủ công) ---
async def collect_single_url_task_async(url: str):
    # Logic xử lý 1 URL nếu cần thiết (có thể bổ sung sau)
    pass