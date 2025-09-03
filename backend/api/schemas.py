"""
Pydantic schemas for VinFast Social Listening Platform API
Request and response models for API endpoints
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

# Request Schemas
class SentimentAnalysisRequest(BaseModel):
    """Request schema for manual sentiment analysis"""
    text: str = Field(..., description="Text to analyze for sentiment", min_length=1, max_length=5000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "VinFast VF8 là một chiếc xe điện tuyệt vời với thiết kế hiện đại"
            }
        }

class CollectionRequest(BaseModel):
    """Request schema for data collection"""
    source: str = Field(..., description="Data source: news, facebook, tiktok, or all")
    max_items: Optional[int] = Field(100, description="Maximum items to collect")
    
class AnalyticsRequest(BaseModel):
    """Request schema for analytics generation"""
    start_date: datetime = Field(..., description="Start date for analysis")
    end_date: datetime = Field(..., description="End date for analysis")
    platforms: Optional[List[str]] = Field(None, description="Platforms to include")

# Response Schemas
class SentimentResult(BaseModel):
    """Sentiment analysis result"""
    sentiment: str = Field(..., description="Sentiment label: positive, negative, neutral")
    confidence_score: float = Field(..., description="Confidence score (0.0 to 1.0)")
    sentiment_score: float = Field(..., description="Sentiment score (-1.0 to 1.0)")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords")

class PostResponse(BaseModel):
    """Response schema for social media posts"""
    id: str = Field(..., description="Post ID")
    platform: str = Field(..., description="Source platform")
    source_name: Optional[str] = Field(None, description="Source name")
    title: Optional[str] = Field(None, description="Post title")
    content: str = Field(..., description="Post content")
    author: Optional[str] = Field(None, description="Post author")
    published_at: datetime = Field(..., description="Publication date")
    collected_at: datetime = Field(..., description="Collection date")
    
    # Engagement metrics
    likes_count: int = Field(0, description="Number of likes")
    shares_count: int = Field(0, description="Number of shares")
    comments_count: int = Field(0, description="Number of comments")
    views_count: int = Field(0, description="Number of views")
    
    # Analysis results
    sentiment: Optional[str] = Field(None, description="Sentiment analysis result")
    sentiment_score: Optional[float] = Field(None, description="Sentiment score")
    confidence_score: Optional[float] = Field(None, description="Analysis confidence")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords")
    topics: List[str] = Field(default_factory=list, description="Identified topics")

class BasicStatistics(BaseModel):
    """Basic statistics schema"""
    total_posts: int
    total_likes: int
    total_shares: int
    total_comments: int
    total_views: int
    total_engagement: int
    avg_engagement: float
    avg_likes_per_post: float
    avg_shares_per_post: float
    avg_comments_per_post: float

class SentimentDistribution(BaseModel):
    """Sentiment distribution schema"""
    positive: int
    negative: int
    neutral: int
    total: int
    positive_percentage: float
    negative_percentage: float
    neutral_percentage: float
    avg_sentiment_score: float
    sentiment_volatility: float

class KeywordData(BaseModel):
    """Keyword analysis data"""
    keyword: str
    count: int
    frequency: float
    avg_sentiment: float
    sentiment_category: str

class PlatformStats(BaseModel):
    """Platform statistics schema"""
    post_count: int
    total_engagement: int
    avg_engagement: float
    sentiment_distribution: Dict[str, Any]

class AnalyticsOverview(BaseModel):
    """Complete analytics overview response"""
    time_period: Dict[str, Any]
    basic_statistics: BasicStatistics
    sentiment_analysis: SentimentDistribution
    platform_breakdown: Dict[str, PlatformStats]
    keyword_analysis: Dict[str, Any]
    topic_analysis: Dict[str, Any]
    engagement_metrics: Dict[str, Any]
    vietnamese_summary: str
    key_insights: List[str]
    generated_at: str

class APIResponse(BaseModel):
    """Generic API response wrapper"""
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    error: Optional[str] = None

class CollectionStatus(BaseModel):
    """Data collection status response"""
    status: str = Field(..., description="Collection status: started, running, completed, error")
    message: str = Field(..., description="Status message in Vietnamese")
    estimated_duration: Optional[str] = Field(None, description="Estimated completion time")
    progress: Optional[Dict[str, Any]] = Field(None, description="Progress information")

class TrendData(BaseModel):
    """Sentiment trend data point"""
    date: str
    total_posts: int
    positive_count: int
    negative_count: int
    neutral_count: int
    avg_sentiment_score: float

class WordCloudData(BaseModel):
    """Word cloud data format"""
    text: str
    value: int
    sentiment: str

class SystemStatus(BaseModel):
    """System health status"""
    database: str
    sentiment_model: str
    api_version: str
    uptime: str
    last_collection: Optional[str]
    processed_posts_today: int

# Error Schemas
class ErrorDetail(BaseModel):
    """Error detail response"""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None

class ValidationError(BaseModel):
    """Validation error response"""
    field: str
    message: str
    invalid_value: Any
