"""
Configuration settings for VinFast Social Listening Platform
(Phiên bản an toàn - Chống lỗi Environment)
"""

import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Social Listening"
    
    # --- DÙNG BIẾN RAW ĐỂ TRÁNH LỖI PARSE JSON ---
    GEMINI_API_KEYS_RAW: str = "AIzaSyCnReMzDZsE7iA0DeE_r7nJyMWculxoqwE" 

    @property
    def GEMINI_API_KEYS(self) -> List[str]:
        """Tự động tách chuỗi thành list"""
        if not self.GEMINI_API_KEYS_RAW:
            return []
        return [k.strip() for k in self.GEMINI_API_KEYS_RAW.split(",") if k.strip()]

    # Model mặc định
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # --- DATABASE ---
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "vinfast_social_listening"
    redis_url: str = "redis://localhost:6379"
    
    # --- API ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    SECRET_KEY: str = "123456"

    # --- Email Configuration (BẮT BUỘC PHẢI THÊM ĐOẠN NÀY) ---
    MAIL_USERNAME: str = "hop20032003@gmail.com"
    MAIL_PASSWORD: str = "shcz dhnz lzuv cclq"
    MAIL_FROM: str = "hop20032003@gmail.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    
    # --- CRAWLER ---
    news_crawl_delay: int = 2
    social_crawl_delay: int = 5
    max_posts_per_batch: int = 100
    
    # --- AI MODEL ---
    model_name: str = "vinai/phobert-base"
    max_sequence_length: int = 256
    
    # --- LOGGING ---
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    # --- CẤU HÌNH PYDANTIC ---
    model_config = SettingsConfigDict(
        env_file=None,  # Không đọc file .env
        extra="ignore",
        case_sensitive=False
    )

# Global settings instance
settings = Settings()