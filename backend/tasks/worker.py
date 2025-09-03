"""
Celery Worker for Background Tasks
Handles data collection and processing tasks asynchronously
"""

from celery import Celery
import asyncio
from datetime import datetime
from loguru import logger

from backend.config.settings import settings
from backend.database.connection import db_manager
from backend.collectors.news_collector import NewsCollector
from backend.collectors.facebook_collector import FacebookCollector
from backend.collectors.tiktok_collector import TikTokCollector
from backend.processors.data_processor import data_processor

# Configure Celery
app = Celery('vinfast-social-listening')
app.conf.update(
    broker_url=settings.redis_url,
    result_backend=settings.redis_url,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Ho_Chi_Minh',
    enable_utc=True,
    task_routes={
        'collect_news': {'queue': 'collection'},
        'collect_facebook': {'queue': 'collection'},
        'collect_tiktok': {'queue': 'collection'},
        'process_sentiment': {'queue': 'processing'},
    },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

@app.task(bind=True, max_retries=3)
def collect_news_task(self):
    """Collect news articles about VinFast"""
    try:
        async def collect():
            await db_manager.connect()
            async with NewsCollector() as collector:
                stats = await collector.collect_all_news()
                logger.info(f"News collection task completed: {stats}")
                return stats
        
        return asyncio.run(collect())
    except Exception as exc:
        logger.error(f"News collection task failed: {exc}")
        raise self.retry(exc=exc, countdown=60, max_retries=3)

@app.task(bind=True, max_retries=3)
def collect_facebook_task(self):
    """Collect Facebook posts about VinFast"""
    try:
        async def collect():
            await db_manager.connect()
            async with FacebookCollector() as collector:
                stats = await collector.collect_all_facebook_data()
                logger.info(f"Facebook collection task completed: {stats}")
                return stats
        
        return asyncio.run(collect())
    except Exception as exc:
        logger.error(f"Facebook collection task failed: {exc}")
        raise self.retry(exc=exc, countdown=60, max_retries=3)

@app.task(bind=True, max_retries=3)
def collect_tiktok_task(self):
    """Collect TikTok posts about VinFast"""
    try:
        async def collect():
            await db_manager.connect()
            async with TikTokCollector() as collector:
                stats = await collector.collect_all_tiktok_data()
                logger.info(f"TikTok collection task completed: {stats}")
                return stats
        
        return asyncio.run(collect())
    except Exception as exc:
        logger.error(f"TikTok collection task failed: {exc}")
        raise self.retry(exc=exc, countdown=60, max_retries=3)

@app.task(bind=True, max_retries=3)
def process_sentiment_task(self, batch_size=50):
    """Process sentiment analysis for unprocessed data"""
    try:
        async def process():
            await db_manager.connect()
            stats = await data_processor.process_unprocessed_data(batch_size)
            logger.info(f"Sentiment processing task completed: {stats}")
            return stats
        
        return asyncio.run(process())
    except Exception as exc:
        logger.error(f"Sentiment processing task failed: {exc}")
        raise self.retry(exc=exc, countdown=30, max_retries=3)

@app.task
def full_collection_pipeline():
    """Run complete data collection and processing pipeline"""
    try:
        logger.info("Starting full collection pipeline...")
        
        # Collect from all sources
        news_result = collect_news_task.delay()
        facebook_result = collect_facebook_task.delay()
        tiktok_result = collect_tiktok_task.delay()
        
        # Wait for collection to complete
        news_stats = news_result.get(timeout=600)  # 10 minutes
        facebook_stats = facebook_result.get(timeout=600)
        tiktok_stats = tiktok_result.get(timeout=600)
        
        # Process sentiment analysis
        processing_result = process_sentiment_task.delay()
        processing_stats = processing_result.get(timeout=300)  # 5 minutes
        
        final_stats = {
            'news': news_stats,
            'facebook': facebook_stats,
            'tiktok': tiktok_stats,
            'processing': processing_stats,
            'completed_at': datetime.now().isoformat()
        }
        
        logger.info(f"Full collection pipeline completed: {final_stats}")
        return final_stats
        
    except Exception as exc:
        logger.error(f"Full collection pipeline failed: {exc}")
        raise

if __name__ == '__main__':
    app.start()
