# backend/tasks/scheduler.py
import schedule
import time
import threading
from loguru import logger
import os
from pymongo import MongoClient # Thêm thư viện này
from backend.collectors.run_collector import collect_data_for_user
from backend.tasks.worker import full_collection_pipeline
from backend.database.connection import db_manager

class TaskScheduler:
    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = None

    def setup_schedules(self):
        """
        Thiết lập lịch chạy dựa trên cấu hình trong Database.
        """
        logger.info("⏳ Đang thiết lập lịch trình (Scheduler)...")
        
        # 1. Kết nối DB để lấy cấu hình động
        crawl_interval = 5 # Mặc định 5 tiếng nếu không tìm thấy config
        
        try:
            # Lấy URL từ biến môi trường
            mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
            db_name = os.getenv("DB_NAME", "vinfast_social_listening")
            
            # Kết nối Sync để lấy config ngay lập tức
            client = MongoClient(mongo_url)
            db = client[db_name]
            config = db["system_config"].find_one()
            
            if config:
                # Ưu tiên lấy social_delay làm chu kỳ chính (theo giờ)
                # Bạn có thể đổi logic này tùy ý
                crawl_interval = config.get("crawl_delay_social", 5)
                logger.success(f"✅ Đã tải cấu hình: Quét định kỳ mỗi {crawl_interval} giờ.")
            else:
                logger.warning("⚠️ Chưa có cấu hình trong DB. Dùng mặc định 5 giờ.")
                
            client.close()
        except Exception as e:
            logger.error(f"❌ Lỗi đọc cấu hình Scheduler: {e}. Dùng mặc định 5 giờ.")

        # 2. Đặt lịch theo giờ (Hours)
        schedule.every(crawl_interval).hours.do(self._schedule_full_pipeline)
        
        # In ra lịch trình để kiểm tra
        logger.info(f"📅 Đã lên lịch: Full Pipeline chạy mỗi {crawl_interval} giờ.")

    def _schedule_full_pipeline(self):
        """Đẩy task vào hàng đợi Celery/Worker"""
        try:
            logger.info("⚡ [SCHEDULER] Kích hoạt chu kỳ quét dữ liệu tự động...")
           # full_collection_pipeline.delay()
            threading.Thread(target=full_collection_pipeline).start()
            logger.success("✅ Task đã được gửi tới Worker thành công")
        except Exception as e:
            logger.error(f"❌ Lỗi khi kích hoạt task: {e}")

    def run(self):
        """Chạy scheduler trong thread riêng"""
        self.setup_schedules()
        
        while not self._stop_event.is_set():
            schedule.run_pending()
            time.sleep(1)

    def start(self):
        if not self._thread or not self._thread.is_alive():
            self._thread = threading.Thread(target=self.run, daemon=True)
            self._thread.start()
            logger.info("🚀 Scheduler service started")

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join()
            logger.info("🛑 Scheduler service stopped")
    # backend/tasks/scheduler.py


async def scheduled_crawl():
    users = await db_manager.database["users"].find({"is_active": True}).to_list(None)
    for user in users:
        user_sources = user.get("active_sources", {"youtube": True, "news": True})
        
        await collect_data_for_user(
            keywords=user.get("keywords", []),
            brand_name=user.get("brand_name"),
            active_sources=user_sources,
            # [CẬP NHẬT] Truyền thêm 2 tham số này
            user_id=str(user["_id"]),
            user_email=user["email"]
        )
# Singleton instance
scheduler = TaskScheduler()