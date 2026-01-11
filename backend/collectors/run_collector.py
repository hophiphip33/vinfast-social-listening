import asyncio
from datetime import datetime, timedelta
import os
import sys
from loguru import logger

from backend.services.email_service import send_crisis_alert_email

# Fix đường dẫn import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.connection import db_manager
from backend.collectors.youtube_collector import search_and_collect_videos
from backend.collectors.news_collector import search_and_collect_news

# Import service ghi log
try:
    from backend.services.logger_service import log_activity
except ImportError:
    log_activity = None

# [FIX 1] Thêm tham số active_sources vào định nghĩa hàm
async def collect_data_for_user(keywords: list, brand_name: str, active_sources: dict = None,user_id: str = None, 
    user_email: str = None):
    start_time = datetime.now()
    """
    Hàm điều phối thu thập dữ liệu cho 1 User cụ thể.
    """
    # 1. Kiểm tra đầu vào
    if not keywords:
        logger.warning("⚠️ Không có từ khóa, bỏ qua thu thập.")
        return

    # 2. Đảm bảo kết nối DB
    if db_manager.database is None:
        await db_manager.connect()

    # 3. --- LẤY BLACKLIST & API KEYS TỪ SYSTEM CONFIG ---
    # (Vẫn cần lấy config hệ thống để lấy API Key, nhưng không lấy active_sources đè lên user nữa)
    blacklist = []
    api_keys = []
    
    try:
        sys_config = await db_manager.database["system_config"].find_one()
        if sys_config:
            blacklist = sys_config.get("blacklist_keywords", [])
            api_keys = sys_config.get("api_keys", [])
            # Chuẩn hóa blacklist
            blacklist = [w.lower().strip() for w in blacklist if w.strip()]
    except Exception as e:
        logger.error(f"❌ Lỗi đọc System Config: {e}")

    # [FIX 2] Xử lý logic ưu tiên nguồn tin
    # Nếu active_sources không được truyền vào (None), mặc định bật hết hoặc lấy từ system
    if active_sources is None:
        active_sources = {"youtube": True, "news": True}

    logger.info(f"🚀 [USER-COLLECT] Brand: {brand_name} | Sources: {active_sources}")
    
    # 4. Ghi log BẮT ĐẦU
    if log_activity:
        # Chỉ ghi log chi tiết nguồn đang chạy
        running_sources = [k for k, v in active_sources.items() if v]
        await log_activity(
            level="INFO",
            actor="SYSTEM",
            action="CRAWL_START",
            details=f"Thu thập cho {brand_name}. Nguồn: {', '.join(running_sources)}"
        )

    # 5. --- TẠO TASK CHẠY SONG SONG DỰA TRÊN active_sources ---
    tasks = []
    skipped_sources = []

    # [FIX 3] Kiểm tra active_sources được truyền vào
    # Youtube Task
    if active_sources.get("youtube", True): # Mặc định là True nếu không tìm thấy key
        tasks.append(search_and_collect_videos(keywords, brand_name, blacklist, api_keys))
    else:
        skipped_sources.append("Youtube")

    # News Task
    if active_sources.get("news", True):
        tasks.append(search_and_collect_news(keywords, brand_name, blacklist, api_keys))
    else:
        skipped_sources.append("News")

    # 6. --- CHẠY VÀ XỬ LÝ KẾT QUẢ ---
    if not tasks:
        msg = f"User {brand_name} đã TẮT tất cả nguồn thu thập."
        logger.warning(msg)
        return

    try:
        # Chạy song song tất cả các task
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.success(f"✅ [USER-COLLECT] Hoàn thành cho {brand_name}!")
        if user_id and user_email:
            await check_and_alert_crisis(user_id, user_email, brand_name, start_time)
        if log_activity:
            details_msg = f"Hoàn tất thu thập cho {brand_name}."
            if skipped_sources:
                details_msg += f" (Đã bỏ qua: {', '.join(skipped_sources)})"
            
            await log_activity("SUCCESS", "SYSTEM", "CRAWL_COMPLETE", details_msg)

    except Exception as e:
        logger.error(f"❌ [USER-COLLECT] Lỗi: {e}")
        if log_activity:
            await log_activity("ERROR", "SYSTEM", "CRAWL_ERROR", f"Lỗi thu thập: {str(e)}")

async def check_and_alert_crisis(user_id: str, email: str, brand_name: str, start_time: datetime):
    """
    Tìm các bài viết Tiêu cực + Điểm cao vừa được thu thập để cảnh báo.
    """
    try:
        # Điều kiện:
        # 1. Thuộc về user này
        # 2. Tạo ra SAU thời điểm bắt đầu quét (tức là bài mới thu thập)
        # 3. Sentiment là NEGATIVE
        # 4. Marketing Score > 6.0 (Ngưỡng nguy hiểm - có thể tùy chỉnh)
        query = {
            "user_id": str(user_id),
            "created_at": {"$gte": start_time},
            "sentiment": "NEGATIVE",
            "marketing_score": {"$gte": 6.0} 
        }
        
        # Tìm trong DB
        cursor = db_manager.database["posts"].find(query).sort("marketing_score", -1).limit(5)
        dangerous_posts = await cursor.to_list(length=5)
        
        if dangerous_posts:
            logger.warning(f"🚨 PHÁT HIỆN {len(dangerous_posts)} BÀI VIẾT NGUY HIỂM CHO {brand_name}")
            
            # 1. Gửi Email
            await send_crisis_alert_email(email, brand_name, dangerous_posts)
            
            # 2. Tạo Notification trong DB (Cho Frontend Pop-up)
            notification_doc = {
                "user_id": str(user_id),
                "type": "CRISIS_ALERT",
                "title": f"Cảnh báo: {len(dangerous_posts)} nội dung tiêu cực mới!",
                "message": f"Phát hiện nội dung tiêu cực có điểm ảnh hưởng cao trên {brand_name}.",
                "data": [
                    {"title": p.get("title"), "url": p.get("source_url"), "score": p.get("marketing_score")} 
                    for p in dangerous_posts
                ],
                "is_read": False,
                "created_at": datetime.now()
            }
            await db_manager.database["notifications"].insert_one(notification_doc)
            
    except Exception as e:
        logger.error(f"Lỗi quy trình cảnh báo: {e}")

async def main_orchestrator():
    """Hàm chạy định kỳ (Cronjob)"""
    pass