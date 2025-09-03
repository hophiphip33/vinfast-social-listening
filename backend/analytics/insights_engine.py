"""
Analytics and Insights Engine for VinFast Social Listening Platform
Generates comprehensive analytics, insights, and summaries in Vietnamese
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import numpy as np
from loguru import logger

from backend.database.connection import DatabaseOperations
from backend.processors.data_processor import data_processor
from backend.config.settings import settings

class InsightsEngine:
    """Generate analytics and insights from collected social media data"""
    
    def __init__(self):
        self.db_ops = DatabaseOperations()
    
    async def generate_comprehensive_report(self, 
                                          start_date: datetime,
                                          end_date: datetime) -> Dict[str, Any]:
        """Generate a comprehensive analytics report"""
        logger.info(f"Generating comprehensive report from {start_date} to {end_date}")
        
        try:
            # Collect all posts from the time period
            posts = await self.db_ops.get_posts(
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                limit=5000
            )
            
            if not posts:
                return self._empty_report()
            
            # Generate different analytics components
            basic_stats = self._calculate_basic_statistics(posts)
            sentiment_analysis = self._analyze_sentiment_distribution(posts)
            platform_breakdown = self._analyze_platform_breakdown(posts)
            keyword_analysis = self._analyze_keywords(posts)
            topic_analysis = self._analyze_topics(posts)
            engagement_metrics = self._calculate_engagement_metrics(posts)
            temporal_trends = await self._analyze_temporal_trends(posts, start_date, end_date)
            
            # Generate Vietnamese insights
            vietnamese_summary = self._generate_vietnamese_summary(
                basic_stats, sentiment_analysis, platform_breakdown, keyword_analysis
            )
            
            key_insights = self._generate_key_insights(
                sentiment_analysis, platform_breakdown, keyword_analysis, engagement_metrics
            )
            
            # Compile final report
            report = {
                "time_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "duration_days": (end_date - start_date).days
                },
                "basic_statistics": basic_stats,
                "sentiment_analysis": sentiment_analysis,
                "platform_breakdown": platform_breakdown,
                "keyword_analysis": keyword_analysis,
                "topic_analysis": topic_analysis,
                "engagement_metrics": engagement_metrics,
                "temporal_trends": temporal_trends,
                "vietnamese_summary": vietnamese_summary,
                "key_insights": key_insights,
                "generated_at": datetime.now().isoformat()
            }
            
            # Save to database
            await self.db_ops.save_analytics_result(report)
            
            logger.info("Comprehensive report generated successfully")
            return report
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            return self._empty_report()
    
    def _calculate_basic_statistics(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate basic statistics from posts"""
        if not posts:
            return {"total_posts": 0, "total_engagement": 0, "avg_engagement": 0}
        
        total_posts = len(posts)
        total_likes = sum(post.get("likes_count", 0) for post in posts)
        total_shares = sum(post.get("shares_count", 0) for post in posts)
        total_comments = sum(post.get("comments_count", 0) for post in posts)
        total_views = sum(post.get("views_count", 0) for post in posts)
        
        total_engagement = total_likes + total_shares + total_comments
        avg_engagement = total_engagement / total_posts if total_posts > 0 else 0
        
        return {
            "total_posts": total_posts,
            "total_likes": total_likes,
            "total_shares": total_shares,
            "total_comments": total_comments,
            "total_views": total_views,
            "total_engagement": total_engagement,
            "avg_engagement": round(avg_engagement, 2),
            "avg_likes_per_post": round(total_likes / total_posts, 2) if total_posts > 0 else 0,
            "avg_shares_per_post": round(total_shares / total_posts, 2) if total_posts > 0 else 0,
            "avg_comments_per_post": round(total_comments / total_posts, 2) if total_posts > 0 else 0
        }
    
    def _analyze_sentiment_distribution(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sentiment distribution"""
        sentiments = [post.get("sentiment", "neutral") for post in posts if post.get("sentiment")]
        sentiment_scores = [post.get("sentiment_score", 0.0) for post in posts if post.get("sentiment_score") is not None]
        
        if not sentiments:
            return {"positive": 0, "negative": 0, "neutral": 0, "total": 0}
        
        distribution = {
            "positive": sentiments.count("positive"),
            "negative": sentiments.count("negative"), 
            "neutral": sentiments.count("neutral"),
            "total": len(sentiments)
        }
        
        # Calculate percentages
        total = distribution["total"]
        distribution.update({
            "positive_percentage": round(distribution["positive"] / total * 100, 2) if total > 0 else 0,
            "negative_percentage": round(distribution["negative"] / total * 100, 2) if total > 0 else 0,
            "neutral_percentage": round(distribution["neutral"] / total * 100, 2) if total > 0 else 0,
            "avg_sentiment_score": round(np.mean(sentiment_scores), 3) if sentiment_scores else 0,
            "sentiment_volatility": round(np.std(sentiment_scores), 3) if len(sentiment_scores) > 1 else 0
        })
        
        return distribution
    
    def _analyze_platform_breakdown(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze data by platform"""
        platform_stats = defaultdict(lambda: {
            "post_count": 0,
            "total_engagement": 0,
            "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
            "avg_sentiment_score": 0.0
        })
        
        for post in posts:
            platform = post.get("platform", "unknown")
            engagement = (post.get("likes_count", 0) + 
                         post.get("shares_count", 0) + 
                         post.get("comments_count", 0))
            sentiment = post.get("sentiment", "neutral")
            
            platform_stats[platform]["post_count"] += 1
            platform_stats[platform]["total_engagement"] += engagement
            platform_stats[platform]["sentiment_distribution"][sentiment] += 1
        
        # Calculate averages
        for platform, stats in platform_stats.items():
            if stats["post_count"] > 0:
                stats["avg_engagement"] = round(stats["total_engagement"] / stats["post_count"], 2)
                
                # Calculate sentiment percentages
                total_sentiments = sum(stats["sentiment_distribution"].values())
                if total_sentiments > 0:
                    for sentiment_type in ["positive", "negative", "neutral"]:
                        count = stats["sentiment_distribution"][sentiment_type]
                        percentage = round(count / total_sentiments * 100, 2)
                        stats["sentiment_distribution"][f"{sentiment_type}_percentage"] = percentage
        
        return dict(platform_stats)
    
    def _analyze_keywords(self, posts: List[Dict[str, Any]], top_k: int = 30) -> Dict[str, Any]:
        """Analyze keyword frequencies and trends"""
        all_keywords = []
        keyword_sentiments = defaultdict(list)
        
        for post in posts:
            keywords = post.get("keywords", [])
            sentiment_score = post.get("sentiment_score", 0.0)
            
            all_keywords.extend(keywords)
            
            # Track sentiment for each keyword
            for keyword in keywords:
                keyword_sentiments[keyword].append(sentiment_score)
        
        # Calculate keyword frequencies
        keyword_counter = Counter(all_keywords)
        keyword_freq = []
        
        for keyword, count in keyword_counter.most_common(top_k):
            scores = keyword_sentiments[keyword]
            avg_sentiment = round(np.mean(scores), 3) if scores else 0.0
            
            keyword_freq.append({
                "keyword": keyword,
                "count": count,
                "frequency": round(count / len(all_keywords), 4) if all_keywords else 0,
                "avg_sentiment": avg_sentiment,
                "sentiment_category": "positive" if avg_sentiment > 0.1 else "negative" if avg_sentiment < -0.1 else "neutral"
            })
        
        return {
            "top_keywords": keyword_freq,
            "total_unique_keywords": len(set(all_keywords)),
            "total_keyword_mentions": len(all_keywords)
        }
    
    def _analyze_topics(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze topic trends and sentiments"""
        topic_stats = defaultdict(lambda: {
            "post_count": 0,
            "sentiment_scores": [],
            "platforms": set()
        })
        
        for post in posts:
            topics = post.get("topics", [])
            sentiment_score = post.get("sentiment_score", 0.0)
            platform = post.get("platform", "unknown")
            
            for topic in topics:
                topic_stats[topic]["post_count"] += 1
                topic_stats[topic]["sentiment_scores"].append(sentiment_score)
                topic_stats[topic]["platforms"].add(platform)
        
        # Format topic analysis
        topic_analysis = []
        for topic, stats in topic_stats.items():
            if stats["post_count"] > 0:
                avg_sentiment = np.mean(stats["sentiment_scores"])
                topic_analysis.append({
                    "topic": topic,
                    "post_count": stats["post_count"],
                    "avg_sentiment": round(avg_sentiment, 3),
                    "sentiment_category": "positive" if avg_sentiment > 0.1 else "negative" if avg_sentiment < -0.1 else "neutral",
                    "platforms": list(stats["platforms"])
                })
        
        # Sort by post count
        topic_analysis.sort(key=lambda x: x["post_count"], reverse=True)
        
        return {
            "topics": topic_analysis[:20],  # Top 20 topics
            "total_topics": len(topic_analysis)
        }
    
    def _calculate_engagement_metrics(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate engagement metrics and patterns"""
        if not posts:
            return {}
        
        engagement_data = []
        platform_engagement = defaultdict(list)
        
        for post in posts:
            total_engagement = (post.get("likes_count", 0) + 
                              post.get("shares_count", 0) + 
                              post.get("comments_count", 0))
            
            engagement_data.append(total_engagement)
            platform_engagement[post.get("platform", "unknown")].append(total_engagement)
        
        # Calculate overall metrics
        metrics = {
            "total_engagement": sum(engagement_data),
            "avg_engagement": round(np.mean(engagement_data), 2),
            "median_engagement": round(np.median(engagement_data), 2),
            "max_engagement": max(engagement_data) if engagement_data else 0,
            "engagement_std": round(np.std(engagement_data), 2) if len(engagement_data) > 1 else 0
        }
        
        # Platform-specific metrics
        platform_metrics = {}
        for platform, engagements in platform_engagement.items():
            if engagements:
                platform_metrics[platform] = {
                    "avg_engagement": round(np.mean(engagements), 2),
                    "total_engagement": sum(engagements),
                    "post_count": len(engagements)
                }
        
        metrics["platform_breakdown"] = platform_metrics
        return metrics
    
    async def _analyze_temporal_trends(self, 
                                     posts: List[Dict[str, Any]], 
                                     start_date: datetime,
                                     end_date: datetime) -> Dict[str, Any]:
        """Analyze temporal trends in the data"""
        try:
            # Generate daily trends
            daily_trends = await data_processor.generate_sentiment_trends(
                start_date, end_date, "daily"
            )
            
            # Find peak activity days
            if daily_trends:
                peak_activity = max(daily_trends, key=lambda x: x["total_posts"])
                peak_positive = max(daily_trends, key=lambda x: x["positive_count"])
                peak_negative = max(daily_trends, key=lambda x: x["negative_count"])
            else:
                peak_activity = peak_positive = peak_negative = None
            
            return {
                "daily_trends": daily_trends,
                "peak_activity_day": peak_activity,
                "most_positive_day": peak_positive,
                "most_negative_day": peak_negative,
                "trend_analysis": self._analyze_trend_direction(daily_trends)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing temporal trends: {e}")
            return {"daily_trends": [], "trend_analysis": "stable"}
    
    def _analyze_trend_direction(self, daily_trends: List[Dict[str, Any]]) -> str:
        """Analyze if sentiment is trending up, down, or stable"""
        if len(daily_trends) < 3:
            return "insufficient_data"
        
        sentiment_scores = [trend["avg_sentiment_score"] for trend in daily_trends]
        
        # Simple linear trend analysis
        x = np.arange(len(sentiment_scores))
        slope = np.polyfit(x, sentiment_scores, 1)[0]
        
        if slope > 0.05:
            return "improving"
        elif slope < -0.05:
            return "declining"
        else:
            return "stable"
    
    def _generate_vietnamese_summary(self, 
                                   basic_stats: Dict[str, Any],
                                   sentiment_analysis: Dict[str, Any],
                                   platform_breakdown: Dict[str, Any],
                                   keyword_analysis: Dict[str, Any]) -> str:
        """Generate summary in Vietnamese"""
        
        total_posts = basic_stats.get("total_posts", 0)
        positive_pct = sentiment_analysis.get("positive_percentage", 0)
        negative_pct = sentiment_analysis.get("negative_percentage", 0)
        
        # Get top platforms
        platforms = list(platform_breakdown.keys())
        top_platform = max(platforms, key=lambda p: platform_breakdown[p]["post_count"]) if platforms else "không xác định"
        
        # Get top keywords
        top_keywords = [kw["keyword"] for kw in keyword_analysis.get("top_keywords", [])[:5]]
        keywords_str = ", ".join(top_keywords) if top_keywords else "không có"
        
        summary = f"""
**Tổng quan về VinFast trong thời gian phân tích:**

Trong khoảng thời gian được phân tích, hệ thống đã thu thập được **{total_posts} bài viết** về VinFast từ các nền tảng mạng xã hội và báo chí trực tuyến.

**Phân tích tình cảm:**
- Tích cực: {positive_pct}% ({sentiment_analysis.get('positive', 0)} bài viết)
- Tiêu cực: {negative_pct}% ({sentiment_analysis.get('negative', 0)} bài viết)  
- Trung tính: {sentiment_analysis.get('neutral_percentage', 0)}% ({sentiment_analysis.get('neutral', 0)} bài viết)

**Nền tảng chính:** {top_platform} là nguồn có nhiều thảo luận nhất về VinFast.

**Từ khóa nổi bật:** {keywords_str}

**Đánh giá tổng quan:** {"Dư luận tích cực" if positive_pct > negative_pct else "Dư luận tiêu cực" if negative_pct > positive_pct else "Dư luận trung tính"} về thương hiệu VinFast trong thời gian này.
        """.strip()
        
        return summary
    
    def _generate_key_insights(self, 
                             sentiment_analysis: Dict[str, Any],
                             platform_breakdown: Dict[str, Any],
                             keyword_analysis: Dict[str, Any],
                             engagement_metrics: Dict[str, Any]) -> List[str]:
        """Generate key insights in Vietnamese"""
        insights = []
        
        # Sentiment insights
        positive_pct = sentiment_analysis.get("positive_percentage", 0)
        negative_pct = sentiment_analysis.get("negative_percentage", 0)
        
        if positive_pct > 60:
            insights.append("Dư luận về VinFast rất tích cực với hơn 60% bài viết mang tính chất tích cực")
        elif negative_pct > 50:
            insights.append("Dư luận về VinFast có xu hướng tiêu cực, cần chú ý để cải thiện hình ảnh thương hiệu")
        elif abs(positive_pct - negative_pct) < 10:
            insights.append("Dư luận về VinFast đang ở trạng thái cân bằng giữa tích cực và tiêu cực")
        
        # Platform insights
        if platform_breakdown:
            top_platform = max(platform_breakdown.keys(), 
                             key=lambda p: platform_breakdown[p]["post_count"])
            top_count = platform_breakdown[top_platform]["post_count"]
            insights.append(f"Nền tảng {top_platform} có nhiều thảo luận nhất về VinFast ({top_count} bài viết)")
        
        # Engagement insights
        avg_engagement = engagement_metrics.get("avg_engagement", 0)
        if avg_engagement > 100:
            insights.append("Mức độ tương tác về VinFast rất cao, cho thấy sự quan tâm lớn từ công chúng")
        elif avg_engagement < 10:
            insights.append("Mức độ tương tác về VinFast tương đối thấp")
        
        # Keyword insights
        top_keywords = keyword_analysis.get("top_keywords", [])
        if top_keywords:
            # Find product-related keywords
            product_keywords = [kw for kw in top_keywords if any(p in kw["keyword"].lower() 
                               for p in ["vf8", "vf9", "vf5", "fadil", "lux"])]
            if product_keywords:
                top_product = product_keywords[0]["keyword"]
                insights.append(f"Sản phẩm '{top_product}' được nhắc đến nhiều nhất trong các cuộc thảo luận")
        
        # Add more insights based on specific patterns
        if len(insights) < 3:
            insights.extend([
                "Thương hiệu VinFast đang nhận được sự quan tâm đáng kể từ cộng đồng mạng",
                "Cần tiếp tục theo dõi và phân tích để hiểu rõ hơn về xu hướng dư luận",
                "Dữ liệu thu thập được cung cấp cái nhìn toàn diện về nhận thức của công chúng"
            ])
        
        return insights[:5]  # Return top 5 insights
    
    def _empty_report(self) -> Dict[str, Any]:
        """Return an empty report structure"""
        return {
            "basic_statistics": {"total_posts": 0},
            "sentiment_analysis": {"positive": 0, "negative": 0, "neutral": 0, "total": 0},
            "platform_breakdown": {},
            "keyword_analysis": {"top_keywords": []},
            "vietnamese_summary": "Không có dữ liệu trong khoảng thời gian được chọn.",
            "key_insights": ["Không đủ dữ liệu để tạo báo cáo phân tích."],
            "generated_at": datetime.now().isoformat()
        }
    
    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics for dashboard"""
        try:
            # Get recent data (last 24 hours)
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=24)
            
            recent_posts = await self.db_ops.get_posts(
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                limit=200
            )
            
            if not recent_posts:
                return {"status": "no_recent_data"}
            
            # Quick statistics
            sentiments = [post.get("sentiment", "neutral") for post in recent_posts]
            total_engagement = sum(
                post.get("likes_count", 0) + 
                post.get("shares_count", 0) + 
                post.get("comments_count", 0) 
                for post in recent_posts
            )
            
            return {
                "last_24h": {
                    "total_posts": len(recent_posts),
                    "positive_posts": sentiments.count("positive"),
                    "negative_posts": sentiments.count("negative"),
                    "neutral_posts": sentiments.count("neutral"),
                    "total_engagement": total_engagement,
                    "avg_sentiment_score": round(np.mean([
                        post.get("sentiment_score", 0.0) for post in recent_posts
                    ]), 3) if recent_posts else 0.0
                },
                "status": "active",
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting real-time metrics: {e}")
            return {"status": "error", "message": str(e)}

# Global insights engine instance
insights_engine = InsightsEngine()

# Usage example
async def main():
    """Example usage"""
    from backend.database.connection import db_manager
    
    await db_manager.connect()
    
    engine = InsightsEngine()
    
    # Generate report for last week
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    report = await engine.generate_comprehensive_report(start_date, end_date)
    print("Vietnamese Summary:")
    print(report["vietnamese_summary"])
    print("\nKey Insights:")
    for insight in report["key_insights"]:
        print(f"- {insight}")
    
    await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
