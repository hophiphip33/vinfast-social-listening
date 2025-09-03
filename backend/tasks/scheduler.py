"""
Automated Task Scheduler
Runs periodic data collection and processing tasks
"""

import asyncio
import schedule
import time
from datetime import datetime
from loguru import logger

from backend.config.settings import settings
from backend.database.connection import db_manager
from backend.tasks.worker import (
    collect_news_task,
    collect_facebook_task,
    collect_tiktok_task,
    process_sentiment_task
)

class TaskScheduler:
    """Manages scheduled tasks for data collection and processing"""
    
    def __init__(self):
        self.is_running = False
    
    def setup_schedules(self):
        """Set up all scheduled tasks"""
        logger.info("Setting up task schedules...")
        
        # Daily data collection (8 AM Vietnam time)
        schedule.every().day.at("08:00").do(self._schedule_daily_collection)
        
        # Process sentiment analysis every 2 hours
        schedule.every(2).hours.do(self._schedule_sentiment_processing)
        
        # Collect news every 4 hours
        schedule.every(4).hours.do(self._schedule_news_collection)
        
        # Collect social media every 6 hours
        schedule.every(6).hours.do(self._schedule_social_collection)
        
        logger.info("Task schedules configured successfully")
    
    def _schedule_daily_collection(self):
        """Schedule daily full collection"""
        try:
            logger.info("Starting scheduled daily collection...")
            
            # Queue collection tasks
            collect_news_task.delay()
            collect_facebook_task.delay()
            collect_tiktok_task.delay()
            
            logger.info("Daily collection tasks queued successfully")
        except Exception as e:
            logger.error(f"Error scheduling daily collection: {e}")
    
    def _schedule_sentiment_processing(self):
        """Schedule sentiment analysis processing"""
        try:
            logger.info("Starting scheduled sentiment processing...")
            process_sentiment_task.delay()
            logger.info("Sentiment processing task queued successfully")
        except Exception as e:
            logger.error(f"Error scheduling sentiment processing: {e}")
    
    def _schedule_news_collection(self):
        """Schedule news collection"""
        try:
            logger.info("Starting scheduled news collection...")
            collect_news_task.delay()
            logger.info("News collection task queued successfully")
        except Exception as e:
            logger.error(f"Error scheduling news collection: {e}")
    
    def _schedule_social_collection(self):
        """Schedule social media collection"""
        try:
            logger.info("Starting scheduled social media collection...")
            collect_facebook_task.delay()
            collect_tiktok_task.delay()
            logger.info("Social media collection tasks queued successfully")
        except Exception as e:
            logger.error(f"Error scheduling social media collection: {e}")
    
    async def initialize_database(self):
        """Initialize database connection"""
        try:
            await db_manager.connect()
            logger.info("Database connection established for scheduler")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def start(self):
        """Start the scheduler"""
        self.is_running = True
        logger.info("Task scheduler started")
        
        # Initialize schedules
        self.setup_schedules()
        
        # Run scheduler loop
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        logger.info("Task scheduler stopped")

# Main scheduler instance
scheduler = TaskScheduler()

async def main():
    """Main entry point for the scheduler"""
    try:
        # Initialize database
        await scheduler.initialize_database()
        
        # Start scheduler (blocking)
        scheduler.start()
        
    except Exception as e:
        logger.error(f"Scheduler startup failed: {e}")
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    logger.info("Starting VinFast Social Listening Task Scheduler...")
    asyncio.run(main())
