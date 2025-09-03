"""
TikTok Public Data Collector for VinFast Social Listening Platform
Collects public TikTok posts and comments about VinFast using free methods
"""

import asyncio
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import aiohttp
from loguru import logger

from backend.database.connection import DatabaseOperations
from backend.config.settings import settings

class TikTokCollector:
    """Collects public TikTok posts and comments about VinFast"""
    
    def __init__(self):
        self.db_ops = DatabaseOperations()
        self.session: Optional[aiohttp.ClientSession] = None
        
        # VinFast related hashtags and keywords
        self.vinfast_hashtags = [
            "#vinfast", "#vinfastvietnam", "#vf8", "#vf9", "#vf5",
            "#xevinfast", "#otosaigon", "#xedien", "#vingroup",
            "#xuhuong", "#otovinfast", "#reviewxe"
        ]
        
        self.vinfast_keywords = [
            "vinfast", "vin fast", "xe vinfast", "ô tô vinfast",
            "xe điện vinfast", "vf8", "vf9", "vf5", "fadil",
            "lux a2.0", "lux sa2.0", "xe hơi vinfast"
        ]
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            headers={
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _is_vinfast_related(self, text: str) -> bool:
        """Check if TikTok content is related to VinFast"""
        if not text:
            return False
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.vinfast_keywords)
    
    async def scrape_hashtag_posts(self, hashtag: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Scrape public posts from a hashtag"""
        collected_posts = []
        
        try:
            logger.info(f"Collecting TikTok posts for hashtag: {hashtag}")
            
            # TikTok hashtag URL (public web interface)
            hashtag_url = f"https://www.tiktok.com/tag/{hashtag.replace('#', '')}"
            
            async with self.session.get(hashtag_url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to access TikTok hashtag {hashtag}: {response.status}")
                    return []
                
                html = await response.text()
                
                # Extract video data from page source
                posts_data = self._extract_posts_from_html(html)
                
                for post_data in posts_data[:limit]:
                    if self._is_vinfast_related(post_data.get("description", "")):
                        processed_post = await self._process_tiktok_post(post_data)
                        if processed_post:
                            collected_posts.append(processed_post)
                
                logger.info(f"Collected {len(collected_posts)} VinFast posts from hashtag {hashtag}")
                
        except Exception as e:
            logger.error(f"Error scraping hashtag {hashtag}: {e}")
        
        return collected_posts
    
    def _extract_posts_from_html(self, html: str) -> List[Dict[str, Any]]:
        """Extract post data from TikTok HTML (simplified approach)"""
        posts = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for script tags containing video data
            scripts = soup.find_all('script', {'id': 'SIGI_STATE'})
            
            for script in scripts:
                try:
                    if script.string:
                        # Parse the JSON data containing video information
                        data = json.loads(script.string)
                        
                        # Extract video items (this structure may change)
                        if 'ItemList' in data:
                            for item_list in data['ItemList'].values():
                                if isinstance(item_list, list):
                                    for item in item_list:
                                        if 'desc' in item:  # Video description
                                            posts.append({
                                                'id': item.get('id'),
                                                'description': item.get('desc', ''),
                                                'author': item.get('author', {}).get('uniqueId', ''),
                                                'likes': item.get('stats', {}).get('diggCount', 0),
                                                'shares': item.get('stats', {}).get('shareCount', 0),
                                                'comments': item.get('stats', {}).get('commentCount', 0),
                                                'views': item.get('stats', {}).get('playCount', 0),
                                                'url': f"https://www.tiktok.com/@{item.get('author', {}).get('uniqueId', '')}/video/{item.get('id', '')}"
                                            })
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            logger.warning(f"Error parsing TikTok HTML: {e}")
        
        return posts
    
    async def _process_tiktok_post(self, raw_post: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process raw TikTok post data into our standard format"""
        try:
            return {
                "platform": "tiktok",
                "source_url": raw_post.get("url"),
                "source_name": "TikTok",
                "title": None,
                "content": raw_post.get("description", ""),
                "author": raw_post.get("author"),
                "likes_count": raw_post.get("likes", 0),
                "shares_count": raw_post.get("shares", 0),
                "comments_count": raw_post.get("comments", 0),
                "views_count": raw_post.get("views", 0),
                "published_at": datetime.now(),  # TikTok doesn't always provide exact timestamp
                "collected_at": datetime.now(),
                "language": "vi",
                "is_processed": False
            }
        except Exception as e:
            logger.error(f"Error processing TikTok post: {e}")
            return None
    
    async def search_public_videos(self, keyword: str, limit: int = 30) -> List[Dict[str, Any]]:
        """Search for public TikTok videos using keywords"""
        collected_posts = []
        
        try:
            logger.info(f"Searching TikTok for keyword: {keyword}")
            
            # TikTok search URL
            search_url = f"https://www.tiktok.com/search/video?q={keyword}"
            
            async with self.session.get(search_url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to search TikTok for '{keyword}': {response.status}")
                    return []
                
                html = await response.text()
                posts_data = self._extract_posts_from_html(html)
                
                for post_data in posts_data[:limit]:
                    processed_post = await self._process_tiktok_post(post_data)
                    if processed_post:
                        collected_posts.append(processed_post)
                
                logger.info(f"Found {len(collected_posts)} posts for keyword '{keyword}'")
                
        except Exception as e:
            logger.error(f"Error searching TikTok for '{keyword}': {e}")
        
        return collected_posts
    
    async def collect_trending_content(self) -> List[Dict[str, Any]]:
        """Collect trending content that might be VinFast related"""
        all_posts = []
        
        try:
            # Collect from hashtags
            for hashtag in self.vinfast_hashtags:
                posts = await self.scrape_hashtag_posts(hashtag, 20)
                all_posts.extend(posts)
                await asyncio.sleep(settings.social_crawl_delay)
            
            # Search for keywords
            for keyword in ["VinFast", "xe điện VinFast", "ô tô VinFast"]:
                posts = await self.search_public_videos(keyword, 15)
                all_posts.extend(posts)
                await asyncio.sleep(settings.social_crawl_delay)
            
            # Remove duplicates based on URL
            unique_posts = []
            seen_urls = set()
            for post in all_posts:
                url = post.get("source_url")
                if url and url not in seen_urls:
                    unique_posts.append(post)
                    seen_urls.add(url)
            
            return unique_posts
            
        except Exception as e:
            logger.error(f"Error collecting trending content: {e}")
            return []
    
    async def collect_all_tiktok_data(self) -> Dict[str, Any]:
        """Main method to collect all TikTok data"""
        logger.info("Starting TikTok data collection...")
        
        all_posts = await self.collect_trending_content()
        
        # Save posts to database
        saved_count = 0
        for post_data in all_posts:
            try:
                await self.db_ops.insert_post(post_data)
                saved_count += 1
            except Exception as e:
                logger.warning(f"Error saving TikTok post: {e}")
        
        collection_stats = {
            "total_posts": len(all_posts),
            "saved_posts": saved_count,
            "hashtags_checked": len(self.vinfast_hashtags),
            "keywords_searched": 3
        }
        
        logger.info(f"TikTok collection completed: {collection_stats}")
        return collection_stats

# Alternative implementation using TikTok API (if available) or web scraping with Selenium
class TikTokSeleniumCollector:
    """More robust TikTok collector using Selenium for dynamic content"""
    
    def __init__(self):
        self.db_ops = DatabaseOperations()
        self.driver = None
    
    async def setup_driver(self):
        """Setup Selenium WebDriver for TikTok scraping"""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        return self.driver
    
    async def scrape_with_selenium(self, url: str) -> List[Dict[str, Any]]:
        """Scrape TikTok using Selenium for dynamic content loading"""
        if not self.driver:
            await self.setup_driver()
        
        try:
            self.driver.get(url)
            await asyncio.sleep(5)  # Wait for page load
            
            # Scroll to load more content
            for _ in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                await asyncio.sleep(2)
            
            # Extract video elements
            video_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-e2e='recommend-list-item']")
            
            posts = []
            for element in video_elements:
                try:
                    # Extract video data from element
                    description = element.find_element(By.CSS_SELECTOR, "[data-e2e='browse-video-desc']").text
                    author = element.find_element(By.CSS_SELECTOR, "[data-e2e='browse-username']").text
                    
                    # Check if VinFast related
                    if any(keyword in description.lower() for keyword in ["vinfast", "vf8", "vf9"]):
                        posts.append({
                            "description": description,
                            "author": author,
                            "url": self.driver.current_url
                        })
                        
                except Exception as e:
                    logger.warning(f"Error extracting video data: {e}")
                    continue
            
            return posts
            
        except Exception as e:
            logger.error(f"Error scraping with Selenium: {e}")
            return []
    
    def cleanup(self):
        """Cleanup resources"""
        if self.driver:
            self.driver.quit()

# Usage example
async def main():
    """Example usage"""
    from backend.database.connection import db_manager
    
    await db_manager.connect()
    
    async with TikTokCollector() as collector:
        stats = await collector.collect_all_tiktok_data()
        print(f"TikTok collection completed: {stats}")
    
    await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
