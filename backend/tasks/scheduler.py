# ... (trong class TaskScheduler)

def setup_schedules(self):
    """Set up all scheduled tasks - Cải tiến thành chu kỳ 5 tiếng"""
    logger.info("Setting up task schedules...")
    
    # Chu kỳ 5 tiếng: Gọi Celery task tổng hợp (full_collection_pipeline)
    schedule.every(5).hours.do(self._schedule_full_pipeline) 
    
    logger.info("Task schedules configured successfully for 5-hour cycle")

def _schedule_full_pipeline(self):
    """Schedule full collection and processing pipeline"""
    try:
        logger.info("Starting scheduled 5-hour collection and processing pipeline...")
        # Sử dụng task full_collection_pipeline đã có trong worker.py
        full_collection_pipeline.delay()
        logger.info("Full collection pipeline task queued successfully")
    except Exception as e:
        logger.error(f"Error scheduling full pipeline: {e}")

# ... (Loại bỏ các hàm _schedule_daily_collection, _schedule_sentiment_processing, v.v.)