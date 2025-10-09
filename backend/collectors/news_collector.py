"""
News Article Collector for VinFast Social Listening Platform
Collects news articles about VinFast from Vietnamese news websites
"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup
from newspaper import Article
import feedparser
from loguru import logger

from backend.database.connection import DatabaseOperations, db_manager
from backend.config.settings import settings


class NewsCollector:
    """Collects news articles about VinFast from Vietnamese news sources"""
    
    def __init__(self):
        self.db_ops = DatabaseOperations()
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Vietnamese news sources (RSS feeds and direct URLs)
        self.news_sources = [
            {
                "name": "VnExpress",
                "rss_url": "https://vnexpress.net/rss/kinh-doanh.rss",
                "base_url": "https://vnexpress.net",
                "search_url": "https://timkiem.vnexpress.net/?q=VinFast"
            },
            {
                "name": "Tuổi Trẻ",
                "rss_url": "https://tuoitre.vn/rss/kinh-te.rss",
                "base_url": "https://tuoitre.vn",
                "search_url": "https://tuoitre.vn/tim-kiem.htm?keywords=VinFast"
            },
            {
                "name": "Thanh Niên",
                "rss_url": "https://thanhnien.vn/rss/kinh-te.rss",
                "base_url": "https://thanhnien.vn",
                "search_url": "https://thanhnien.vn/tim-kiem?q=VinFast"
            },
            {
                "name": "Vietnamnet",
                "rss_url": "https://vietnamnet.vn/rss/kinh-te.rss",
                "base_url": "https://vietnamnet.vn",
                "search_url": "https://vietnamnet.vn/tim-kiem?q=VinFast"
            }
        ]
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def collect_from_rss(self, source: Dict[str, str]) -> List[Dict[str, Any]]:
        """Collect articles from RSS feed"""
        try:
            async with self.session.get(source["rss_url"]) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch RSS from {source['name']}: {response.status}")
                    return []
                
                content = await response.text()
                feed = feedparser.parse(content)
                
                articles = []
                for entry in feed.entries:
                    # Filter articles that mention VinFast
                    if self._is_vinfast_related(entry.title + " " + getattr(entry, 'summary', '')):
                        article_data = await self._extract_article_details(entry.link, source)
                        if article_data:
                            articles.append(article_data)
                
                logger.info(f"Collected {len(articles)} VinFast articles from {source['name']}")
                return articles
                
        except Exception as e:
            logger.error(f"Error collecting from RSS {source['name']}: {e}")
            return []
    
    async def collect_from_search(self, source: Dict[str, str]) -> List[Dict[str, Any]]:
        """Collect articles from search results"""
        try:
            async with self.session.get(source["search_url"]) as response:
                if response.status != 200:
                    logger.warning(f"Failed to search {source['name']}: {response.status}")
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                articles = []
                article_links = self._extract_article_links(soup, source)
                
                for link in article_links[:10]:  # Limit to 10 articles per source
                    article_data = await self._extract_article_details(link, source)
                    if article_data:
                        articles.append(article_data)
                    
                    # Delay between requests to be respectful
                    await asyncio.sleep(settings.news_crawl_delay)
                
                logger.info(f"Collected {len(articles)} VinFast articles from search in {source['name']}")
                return articles
                
        except Exception as e:
            logger.error(f"Error collecting from search {source['name']}: {e}")
            return []
    
    def _is_vinfast_related(self, text: str) -> bool:
        """Check if article content is related to VinFast"""
        vinfast_keywords = [
            "vinfast", "vin fast", "xe vinfast", "ô tô vinfast",
            "vingroup", "phạm nhật vượng", "xe điện vinfast",
            "vf8", "vf9", "vf5", "fadil", "lux a2.0", "lux sa2.0"
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in vinfast_keywords)
    
    def _extract_article_links(self, soup: BeautifulSoup, source: Dict[str, str]) -> List[str]:
        """Extract article links from search results (customize per news site)"""
        links = []
        
        for link_tag in soup.find_all('a', href=True):
            href = link_tag['href']
            if href.startswith('/'):
                href = source['base_url'] + href
            elif not href.startswith('http'):
                continue
                
            if source['base_url'] in href and self._is_article_url(href):
                links.append(href)
        
        return list(set(links))  # Remove duplicates
    
    def _is_article_url(self, url: str) -> bool:
        """Check if URL appears to be an article"""
        article_indicators = ['-', '_', '.html', '/detail/', '/post/', '/news/']
        return any(indicator in url for indicator in article_indicators)
    
    async def _extract_article_details(self, url: str, source: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Extract full article content from URL (async-safe)"""
        try:
            # Dùng aiohttp thay vì newspaper3k để tránh blocking
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch article: {url}")
                    return None
                html = await response.text()

            # Phân tích nội dung bằng BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            
            title = soup.find("title").get_text(strip=True) if soup.find("title") else None
            content = " ".join(p.get_text(strip=True) for p in soup.find_all("p"))
            
            if not title or not self._is_vinfast_related(title + " " + content):
                return None

            return {
                "platform": "news",
                "source_url": url,
                "source_name": source["name"],
                "title": title,
                "content": content,
                "author": None,  # có thể bổ sung nếu tìm được trong meta
                "published_at": datetime.now(),  # fallback
                "collected_at": datetime.now(),
                "likes_count": 0,
                "shares_count": 0,
                "comments_count": 0,
                "views_count": 0,
                "language": "vi",
                "is_processed": False
            }

        except Exception as e:
            logger.error(f"Error extracting article from {url}: {e}")
            return None

    
    async def collect_all_news(self) -> Dict[str, int]:
        """Collect news from all sources"""
        total_collected = 0
        source_stats = {}
        
        logger.info("Starting news collection for VinFast...")
        
        for source in self.news_sources:
            try:
                rss_articles = await self.collect_from_rss(source)
                search_articles = await self.collect_from_search(source)
                
                all_articles = rss_articles + search_articles
                
                # Remove duplicates based on URL
                unique_articles = []
                seen_urls = set()
                for article in all_articles:
                    if article["source_url"] not in seen_urls:
                        unique_articles.append(article)
                        seen_urls.add(article["source_url"])
                
                # Save to database
                saved_count = 0
                for article in unique_articles:
                    try:
                        if db_manager.database is None:
                            logger.error("Database is not connected, cannot save article")
                            continue
                        
                        await self.db_ops.insert_post(article)
                        saved_count += 1
                    except Exception as e:
                        logger.warning(f"Duplicate or error saving article: {e}")
                
                source_stats[source["name"]] = saved_count
                total_collected += saved_count
                
                logger.info(f"Saved {saved_count} new articles from {source['name']}")
                await asyncio.sleep(2)  # Delay between sources
                
            except Exception as e:
                logger.error(f"Error collecting from {source['name']}: {e}")
                source_stats[source["name"]] = 0
        
        logger.info(f"Total news articles collected: {total_collected}")
        return {"total": total_collected, "sources": source_stats}


# Usage example
async def main():
    """Example usage"""
    await db_manager.connect()
    
    async with NewsCollector() as collector:
        stats = await collector.collect_all_news()
        print(f"Collection completed: {stats}")
    
    await db_manager.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
