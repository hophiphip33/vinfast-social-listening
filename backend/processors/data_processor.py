"""
Data Processing Pipeline for VinFast Social Listening Platform
Handles data cleaning, preprocessing, and sentiment analysis
"""

import asyncio
from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import Counter
import numpy as np
from loguru import logger

from backend.database.connection import DatabaseOperations
from backend.processors.vietnamese_sentiment import sentiment_analyzer
from backend.config.settings import settings

class DataProcessor:
    """Main data processing pipeline"""
    
    def __init__(self):
        self.db_ops = DatabaseOperations()
        self.sentiment_analyzer = sentiment_analyzer
    
    async def process_unprocessed_data(self, batch_size: int = 50) -> Dict[str, Any]:
        """Process unprocessed posts and comments"""
        logger.info("Starting data processing pipeline...")
        
        # Get unprocessed posts
        unprocessed_posts = await self.db_ops.get_unprocessed_posts(batch_size)
        
        if not unprocessed_posts:
            logger.info("No unprocessed posts found")
            return {"processed_posts": 0, "processed_comments": 0}
        
        logger.info(f"Processing {len(unprocessed_posts)} posts...")
        
        processed_count = 0
        for post in unprocessed_posts:
            try:
                await self._process_single_post(post)
                processed_count += 1
                
                # Delay between processing to avoid overwhelming resources
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error processing post {post.get('_id')}: {e}")
                continue
        
        logger.info(f"Processed {processed_count} posts successfully")
        return {"processed_posts": processed_count, "processed_comments": 0}
    
    async def _process_single_post(self, post: Dict[str, Any]):
        """Process a single post for sentiment analysis and keyword extraction"""
        try:
            content = post.get("content", "")
            title = post.get("title", "")
            full_text = f"{title} {content}".strip()
            
            if not full_text:
                logger.warning(f"Empty content for post {post.get('_id')}")
                return
            
            # Clean and preprocess text
            cleaned_text = self._clean_text(full_text)
            
            # Perform sentiment analysis
            sentiment_result = await self.sentiment_analyzer.analyze_sentiment(cleaned_text)
            
            # Extract keywords
            keywords = self.sentiment_analyzer.extract_keywords(cleaned_text, top_k=15)
            
            # Extract VinFast-specific topics
            topics = self._extract_topics(cleaned_text)
            
            # Prepare analysis data
            analysis_data = {
                "sentiment": sentiment_result["sentiment"],
                "sentiment_score": sentiment_result["sentiment_score"],
                "confidence_score": sentiment_result["confidence_score"],
                "keywords": keywords,
                "topics": topics,
                "processed_at": datetime.now()
            }
            
            # Update post in database
            await self.db_ops.update_post_analysis(post["_id"], analysis_data)
            
            logger.debug(f"Successfully processed post {post['_id']} - Sentiment: {sentiment_result['sentiment']}")
            
        except Exception as e:
            logger.error(f"Error processing post {post.get('_id')}: {e}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize Vietnamese text"""
        if not text:
            return ""
        
        # Remove HTML tags
        import re
        text = re.sub(r'<[^>]+>', '', text)
        
        # Normalize Vietnamese characters
        text = self._normalize_vietnamese(text)
        
        # Remove excessive punctuation
        text = re.sub(r'[.]{3,}', '...', text)
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _normalize_vietnamese(self, text: str) -> str:
        """Normalize Vietnamese diacritics and characters"""
        # Handle common Vietnamese character variations
        replacements = {
            'đ': 'd', 'Đ': 'D',  # Optional: keep Vietnamese characters
            # Add more normalizations if needed
        }
        
        # For now, keep Vietnamese characters as they are important for sentiment
        return text
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract VinFast-related topics from text"""
        topics = []
        
        # VinFast product topics
        product_keywords = {
            'vf8': 'VF8 Electric SUV',
            'vf9': 'VF9 Electric SUV', 
            'vf5': 'VF5 Electric Car',
            'fadil': 'VinFast Fadil',
            'lux a2.0': 'VinFast Lux A2.0',
            'lux sa2.0': 'VinFast Lux SA2.0',
            'klara': 'VinFast Klara Electric Scooter'
        }
        
        # Business topics
        business_keywords = {
            'bán hàng': 'Sales',
            'kinh doanh': 'Business',
            'xuất khẩu': 'Export',
            'thị trường': 'Market',
            'cổ phiếu': 'Stock',
            'đầu tư': 'Investment',
            'nhà máy': 'Factory',
            'sản xuất': 'Manufacturing'
        }
        
        # Technical topics
        tech_keywords = {
            'xe điện': 'Electric Vehicle',
            'pin xe điện': 'EV Battery',
            'sạc xe điện': 'EV Charging',
            'tự lái': 'Autonomous Driving',
            'công nghệ': 'Technology',
            'an toàn': 'Safety'
        }
        
        text_lower = text.lower()
        
        # Check for product topics
        for keyword, topic in product_keywords.items():
            if keyword in text_lower:
                topics.append(topic)
        
        # Check for business topics
        for keyword, topic in business_keywords.items():
            if keyword in text_lower:
                topics.append(topic)
        
        # Check for tech topics
        for keyword, topic in tech_keywords.items():
            if keyword in text_lower:
                topics.append(topic)
        
        return list(set(topics))  # Remove duplicates
    
    async def generate_keyword_frequency(self, 
                                       start_date: datetime,
                                       end_date: datetime,
                                       top_k: int = 50) -> List[Dict[str, Any]]:
        """Generate keyword frequency analysis for a time period"""
        try:
            # Get posts from the specified time period
            posts = await self.db_ops.get_posts(
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                limit=1000  # Adjust as needed
            )
            
            # Collect all keywords
            all_keywords = []
            for post in posts:
                keywords = post.get("keywords", [])
                all_keywords.extend(keywords)
            
            # Count keyword frequencies
            keyword_counter = Counter(all_keywords)
            
            # Format results
            keyword_freq = [
                {"keyword": keyword, "count": count, "frequency": count / len(all_keywords)}
                for keyword, count in keyword_counter.most_common(top_k)
            ]
            
            logger.info(f"Generated keyword frequency for {len(posts)} posts, top {top_k} keywords")
            return keyword_freq
            
        except Exception as e:
            logger.error(f"Error generating keyword frequency: {e}")
            return []
    
    async def generate_sentiment_trends(self,
                                      start_date: datetime,
                                      end_date: datetime,
                                      interval: str = "daily") -> List[Dict[str, Any]]:
        """Generate sentiment trends over time"""
        try:
            posts = await self.db_ops.get_posts(
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                limit=2000
            )
            
            # Group posts by time interval
            if interval == "daily":
                delta = timedelta(days=1)
            elif interval == "weekly":
                delta = timedelta(weeks=1)
            else:
                delta = timedelta(hours=1)
            
            trends = []
            current_date = start_date
            
            while current_date < end_date:
                next_date = current_date + delta
                
                # Filter posts for this time period
                period_posts = [
                    post for post in posts
                    if current_date <= datetime.fromisoformat(post["published_at"]) < next_date
                ]
                
                if period_posts:
                    # Calculate sentiment distribution
                    sentiments = [post.get("sentiment", "neutral") for post in period_posts]
                    sentiment_scores = [post.get("sentiment_score", 0.0) for post in period_posts]
                    
                    trend_data = {
                        "date": current_date.isoformat(),
                        "total_posts": len(period_posts),
                        "positive_count": sentiments.count("positive"),
                        "negative_count": sentiments.count("negative"),
                        "neutral_count": sentiments.count("neutral"),
                        "avg_sentiment_score": np.mean(sentiment_scores) if sentiment_scores else 0.0
                    }
                    
                    trends.append(trend_data)
                
                current_date = next_date
            
            logger.info(f"Generated sentiment trends for {len(trends)} time periods")
            return trends
            
        except Exception as e:
            logger.error(f"Error generating sentiment trends: {e}")
            return []

# Global data processor instance
data_processor = DataProcessor()

# Usage example
async def main():
    """Example usage"""
    from backend.database.connection import db_manager
    
    await db_manager.connect()
    
    processor = DataProcessor()
    stats = await processor.process_unprocessed_data()
    print(f"Processing completed: {stats}")
    
    await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
