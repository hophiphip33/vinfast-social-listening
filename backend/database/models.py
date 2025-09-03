"""
Database models for VinFast Social Listening Platform
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from pymongo import MongoClient
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class SocialMediaPost(BaseModel):
    """Model for social media posts and news articles"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    # Source information
    platform: str  # "facebook", "tiktok", "news"
    source_url: Optional[str] = None
    source_name: Optional[str] = None
    
    # Content
    title: Optional[str] = None
    content: str
    author: Optional[str] = None
    
    # Engagement metrics
    likes_count: int = 0
    shares_count: int = 0
    comments_count: int = 0
    views_count: int = 0
    
    # Temporal data
    published_at: datetime
    collected_at: datetime = Field(default_factory=datetime.now)
    
    # Analysis results
    sentiment: Optional[str] = None  # "positive", "negative", "neutral"
    sentiment_score: Optional[float] = None  # -1.0 to 1.0
    confidence_score: Optional[float] = None  # 0.0 to 1.0
    keywords: List[str] = []
    topics: List[str] = []
    
    # Metadata
    language: str = "vi"  # Vietnamese
    is_processed: bool = False
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class Comment(BaseModel):
    """Model for comments on social media posts"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    # Reference to parent post
    post_id: PyObjectId
    parent_comment_id: Optional[PyObjectId] = None  # For nested comments
    
    # Content
    content: str
    author: Optional[str] = None
    
    # Engagement
    likes_count: int = 0
    replies_count: int = 0
    
    # Temporal data
    published_at: datetime
    collected_at: datetime = Field(default_factory=datetime.now)
    
    # Analysis results
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    confidence_score: Optional[float] = None
    
    # Metadata
    language: str = "vi"
    is_processed: bool = False
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class AnalyticsResult(BaseModel):
    """Model for analytics and insights"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    # Time period
    start_date: datetime
    end_date: datetime
    
    # Metrics
    total_posts: int
    total_comments: int
    total_engagement: int
    
    # Sentiment analysis
    positive_count: int
    negative_count: int
    neutral_count: int
    avg_sentiment_score: float
    
    # Top keywords and topics
    top_keywords: List[Dict[str, Any]]  # [{"keyword": "word", "count": 123}]
    trending_topics: List[str]
    
    # Platform breakdown
    platform_stats: Dict[str, Dict[str, Any]]
    
    # Generated insights
    summary: str  # Vietnamese summary
    insights: List[str]  # Key insights in Vietnamese
    
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class DataSource(BaseModel):
    """Model for tracking data sources"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    name: str
    platform: str
    url: str
    is_active: bool = True
    last_crawled: Optional[datetime] = None
    total_collected: int = 0
    
    # Configuration
    crawl_frequency: str = "daily"  # "hourly", "daily", "weekly"
    max_posts: int = 100
    
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
