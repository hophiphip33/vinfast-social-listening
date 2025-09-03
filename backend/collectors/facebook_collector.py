"""
Facebook Public Data Collector for VinFast Social Listening Platform
Collects public posts and comments about VinFast from Facebook using free methods
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re
from bs4 import BeautifulSoup
import aiohttp
from facebook_scraper import get_posts
from loguru import logger

from backend.database.connection import DatabaseOperations
from backend.config.settings import settings

class FacebookCollector:
    """Collects public Facebook posts and comments about VinFast"""
    
    def __init__(self):
        self.db_ops = DatabaseOperations()
        self.session: Optional[aiohttp.ClientSession] = None
        
        # VinFast related keywords in Vietnamese
        self.vinfast_keywords = [
            "vinfast", "vin fast", "xe vinfast", "ô tô vinfast",
            "xe điện vinfast", "vingroup", "phạm nhật vượng",
            "vf8", "vf9", "vf5", "fadil", "lux a2.0", "lux sa2.0",
            "xe hơi vinfast", "oto vinfast", "vinfast vietnam"
        ]
        
        # Public Facebook pages to monitor
        self.target_pages = [
            "VinFast",
            "VinFastGlobal", 
            "VinGroupOfficial",
            "otosaigon",
            "xehay.vn",
            "autodaily.vn",
            # Add more relevant pages
        ]
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _is_vinfast_related(self, text: str) -> bool:
        """Check if post content is related to VinFast"""
        if not text:
            return False
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.vinfast_keywords)
    
    def _extract_engagement_metrics(self, post_data: Dict[str, Any]) -> Dict[str, int]:
        """Extract engagement metrics from post data"""
        return {
            "likes_count": post_data.get("likes", 0) or 0,
            "shares_count": post_data.get("shares", 0) or 0,
            "comments_count": post_data.get("comments", 0) or 0,
            "views_count": 0  # Not available in free version
        }
    
    async def collect_from_page(self, page_name: str, max_posts: int = 20) -> List[Dict[str, Any]]:
        """Collect public posts from a Facebook page"""
        collected_posts = []
        
        try:
            logger.info(f"Collecting posts from Facebook page: {page_name}")
            
            # Use facebook-scraper library for public posts
            posts = get_posts(
                account=page_name,
                pages=max_posts // 10,  # Approximate pages needed
                extra_info=True,
                timeout=30
            )
            
            for post in posts:
                try:
                    # Check if post is VinFast related
                    post_text = (post.get("text") or "") + " " + (post.get("post_text") or "")
                    
                    if not self._is_vinfast_related(post_text):
                        continue
                    
                    # Extract engagement metrics
                    engagement = self._extract_engagement_metrics(post)
                    
                    # Prepare post data
                    post_data = {
                        "platform": "facebook",
                        "source_url": post.get("post_url"),
                        "source_name": page_name,
                        "title": None,  # Facebook posts don't have titles
                        "content": post_text.strip(),
                        "author": page_name,
                        "published_at": post.get("time") or datetime.now(),
                        "collected_at": datetime.now(),
                        **engagement,
                        "language": "vi",
                        "is_processed": False
                    }
                    
                    collected_posts.append(post_data)
                    
                    # Collect comments if available
                    if post.get("comments_full"):
                        await self._collect_comments(post, post_data)
                    
                    # Delay to avoid rate limiting
                    await asyncio.sleep(settings.social_crawl_delay)
                    
                except Exception as e:
                    logger.warning(f"Error processing post from {page_name}: {e}")
                    continue
            
            logger.info(f"Collected {len(collected_posts)} VinFast-related posts from {page_name}")
            return collected_posts
            
        except Exception as e:
            logger.error(f"Error collecting from Facebook page {page_name}: {e}")
            return []
    
    async def _collect_comments(self, post: Dict[str, Any], post_data: Dict[str, Any]):
        """Collect comments from a Facebook post"""
        try:
            if not post.get("comments_full"):
                return
            
            for comment in post["comments_full"]:
                try:
                    comment_text = comment.get("comment_text", "")
                    
                    if not comment_text.strip():
                        continue
                    
                    comment_data = {
                        "post_id": post_data.get("_id"),  # Will be set after post is saved
                        "content": comment_text,
                        "author": comment.get("commenter_name"),
                        "likes_count": comment.get("comment_reaction_count", 0) or 0,
                        "replies_count": len(comment.get("replies", [])),
                        "published_at": comment.get("comment_time") or datetime.now(),
                        "collected_at": datetime.now(),
                        "language": "vi",
                        "is_processed": False
                    }
                    
                    # Save comment to database (will need post_id after post is saved)
                    # For now, store in a temporary list or handle after post insertion
                    
                except Exception as e:
                    logger.warning(f"Error processing comment: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error collecting comments: {e}")
    
    async def search_public_posts(self, query: str = "VinFast", limit: int = 50) -> List[Dict[str, Any]]:
        """Search for public posts containing VinFast keywords"""
        collected_posts = []
        
        try:
            # Use Facebook's public search (this is a simplified approach)
            # In practice, you might need to use Selenium for more complex scraping
            
            search_queries = [
                "VinFast xe điện",
                "VinFast ô tô",
                "VinFast VF8",
                "VinFast VF9",
                "xe VinFast"
            ]
            
            for search_query in search_queries:
                try:
                    # This is a placeholder for public post search
                    # You would implement specific scraping logic here
                    logger.info(f"Searching for posts with query: {search_query}")
                    
                    # Simulated search result processing
                    # In real implementation, you would scrape search results
                    
                    await asyncio.sleep(settings.social_crawl_delay)
                    
                except Exception as e:
                    logger.warning(f"Error searching for '{search_query}': {e}")
                    continue
            
            return collected_posts
            
        except Exception as e:
            logger.error(f"Error in public post search: {e}")
            return []
    
    async def collect_all_facebook_data(self) -> Dict[str, Any]:
        """Main method to collect all Facebook data"""
        all_posts = []
        collection_stats = {"pages": {}, "total_posts": 0, "total_comments": 0}
        
        logger.info("Starting Facebook data collection...")
        
        # Collect from target pages
        for page_name in self.target_pages:
            try:
                posts = await self.collect_from_page(page_name, settings.max_posts_per_batch)
                all_posts.extend(posts)
                collection_stats["pages"][page_name] = len(posts)
                
                # Save posts to database
                saved_count = 0
                for post_data in posts:
                    try:
                        post_id = await self.db_ops.insert_post(post_data)
                        saved_count += 1
                    except Exception as e:
                        logger.warning(f"Error saving post: {e}")
                
                logger.info(f"Saved {saved_count} posts from {page_name}")
                
            except Exception as e:
                logger.error(f"Error collecting from page {page_name}: {e}")
                collection_stats["pages"][page_name] = 0
        
        collection_stats["total_posts"] = len(all_posts)
        
        logger.info(f"Facebook collection completed. Total posts: {collection_stats['total_posts']}")
        return collection_stats

# Alternative implementation using Selenium for more robust scraping
class FacebookSeleniumCollector:
    """Alternative Facebook collector using Selenium for JavaScript-heavy pages"""
    
    def __init__(self):
        self.db_ops = DatabaseOperations()
        self.driver = None
    
    async def setup_driver(self):
        """Setup Selenium WebDriver"""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        return self.driver
    
    def cleanup_driver(self):
        """Cleanup Selenium WebDriver"""
        if self.driver:
            self.driver.quit()

# Usage example
async def main():
    """Example usage"""
    from backend.database.connection import db_manager
    
    await db_manager.connect()
    
    async with FacebookCollector() as collector:
        stats = await collector.collect_all_facebook_data()
        print(f"Facebook collection completed: {stats}")
    
    await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
