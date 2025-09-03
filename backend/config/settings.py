"""
Configuration settings for VinFast Social Listening Platform
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Database
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "vinfast_social_listening"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    secret_key: str = "your-secret-key-change-this-in-production"
    
    # Data Collection
    news_crawl_delay: int = 2
    social_crawl_delay: int = 5
    max_posts_per_batch: int = 100
    
    # Sentiment Analysis
    model_name: str = "vinai/phobert-base"
    max_sequence_length: int = 256
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    # Social Media (Optional for public data)
    fb_email: Optional[str] = None
    fb_password: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
