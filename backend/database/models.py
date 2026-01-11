"""
Database models & API Schemas for VinFast Social Listening Platform
Updated for Pydantic v2 compatibility
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, GetJsonSchemaHandler
from bson import ObjectId
from pydantic_core import core_schema

# ==============================================================================
# 1. CUSTOM TYPES (CHO MONGODB & PYDANTIC V2)
# ==============================================================================
class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: Any
    ) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(ObjectId),
                ]),
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> Any:
        return {"type": "string"}

# ==============================================================================
# 2. API SCHEMAS (QUAN TRỌNG: PHẦN NÀY ĐANG BỊ THIẾU GÂY LỖI)
# ==============================================================================

class UserCreate(BaseModel):
    """Schema dùng để nhận dữ liệu khi tạo user mới (Input)"""
    email: str
    password: Optional[str] = None
    username: str
    role: str = "user"  # "admin" hoặc "user"
    keywords: List[str] = []
    brand_name: Optional[str] = "VinFast"

class UserResponse(BaseModel):
    """Schema dùng để trả về thông tin user cho Frontend (Output)"""
    id: str
    email: str
    username: str
    role: str
    is_active: bool
    keywords: List[str] = []
    brand_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    """Schema cho Token đăng nhập"""
    access_token: str
    token_type: str
    role: str

# ==============================================================================
# 3. DATABASE MODELS (LƯU TRONG MONGODB)
# ==============================================================================

class User(BaseModel):
    """Model User lưu trong Database (Có password đã hash)"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    email: str
    username: str
    password: str  # Hashed password
    role: str = "user"
    
    keywords: List[str] = []
    brand_name: Optional[str] = None
    active_sources: Dict[str, bool] = {"youtube": True, "news": True}
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class SocialMediaPost(BaseModel):
    """Model bài đăng (News, Youtube, Facebook...)"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    
    platform: str  # "youtube", "news"
    source_url: Optional[str] = None
    source_name: Optional[str] = None
    
    title: Optional[str] = None
    content: str
    author: Optional[str] = None
    
    # Engagement metrics
    likes_count: int = 0
    shares_count: int = 0
    comments_count: int = 0
    views_count: int = 0
    dislikes_count: int = 0
    
    # Temporal data
    published_at: datetime
    collected_at: datetime = Field(default_factory=datetime.now)
    
    # Analysis results
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    confidence_score: Optional[float] = None
    
    # Điểm số Marketing
    ai_sentiment_raw: Optional[float] = None
    crowd_sentiment: Optional[float] = None
    reaction_score: Optional[float] = None
    marketing_score: Optional[float] = None
    
    keywords: List[str] = []
    brand_name: Optional[str] = None # Để lọc theo brand
    
    # Metadata
    language: str = "vi"
    is_processed: bool = False
    extra_data: Dict[str, Any] = {} 
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class Comment(BaseModel):
    """Model bình luận"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    post_id: PyObjectId # Link tới bài viết gốc
    parent_comment_id: Optional[PyObjectId] = None
    
    content: str
    author: Optional[str] = None
    
    likes_count: int = 0
    replies_count: int = 0
    
    published_at: datetime
    collected_at: datetime = Field(default_factory=datetime.now)
    
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    confidence_score: Optional[float] = None
    
    language: str = "vi"
    is_processed: bool = False
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class AnalyticsResult(BaseModel):
    """Model thống kê"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    
    start_date: datetime
    end_date: datetime
    
    total_posts: int
    total_comments: int
    total_engagement: int
    
    positive_count: int
    negative_count: int
    neutral_count: int
    avg_sentiment_score: float
    
    top_keywords: List[Dict[str, Any]]
    trending_topics: List[str]
    platform_stats: Dict[str, Dict[str, Any]]
    
    summary: str
    insights: List[str]
    
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class DataSource(BaseModel):
    """Model nguồn dữ liệu"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    
    name: str
    platform: str
    url: str
    is_active: bool = True
    last_crawled: Optional[datetime] = None
    total_collected: int = 0
    
    crawl_frequency: str = "daily"
    max_posts: int = 100
    
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class SystemLog(BaseModel):
    """Model nhật ký hệ thống"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    
    level: str 
    actor: str 
    action: str
    details: str
    
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class SystemConfiguration(BaseModel):
    """Model cấu hình hệ thống"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    
    # Crawl Settings
    crawl_delay_news: int = 24
    crawl_delay_social: int = 24
    max_posts_batch: int = 50
    active_sources: Dict[str, bool] = {"youtube": True, "news": True, "facebook": False}
    
    # AI Settings
    api_keys: List[str] = [] 
    active_model: str = "gemini-1.5-flash"
    
    # Security
    blacklist_keywords: List[str] = []
    blocked_domains: List[str] = []
    
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True