import csv
import io
import os
import sys
import math
import secrets
import string
import traceback
import requests
import re
import asyncio
from typing import List, Optional, Dict
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from bson import ObjectId
from bs4 import BeautifulSoup

# --- 3RD PARTY LIBRARIES ---
import google.generativeai as genai
from yt_dlp import YoutubeDL
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

# --- SETUP PATH & IMPORTS ---
# Fix đường dẫn import để Python tìm thấy module 'backend'
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.api.schemas import UserSettingsUpdate, UserResponse, TokenResponse
from backend.database.connection import db_manager
from backend.database.models import UserCreate, SystemLog, SystemConfiguration
from backend.services.auth import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    get_current_user,
    Token
)
from backend.config.settings import settings
from backend.services.logger_service import log_activity
from backend.tasks.scheduler import scheduler
from backend.api.security import get_current_user
from backend.processors.custom_ai import CustomSentimentModel

# Import Service Email & Collector (Xử lý lỗi nếu chưa cấu hình)
try:
    from backend.services.email_service import send_new_account_email, send_reset_password_email
except ImportError:
    send_new_account_email = None
    send_reset_password_email = None

try:
    from backend.collectors.run_collector import collect_data_for_user, main_orchestrator
except ImportError:
    collect_data_for_user = None
    main_orchestrator = None

# ==============================================================================
# 1. KHỞI TẠO APP & CONFIG
# ==============================================================================

app = FastAPI(title=settings.PROJECT_NAME)

# Cấu hình CORS (Cho phép Frontend gọi API)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo AI Model & Gemini
sentiment_model = CustomSentimentModel()
genai.configure(api_key=settings.GEMINI_API_KEYS[0] if settings.GEMINI_API_KEYS else "")
gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)

# ==============================================================================
# 2. LOCAL SCHEMAS (MODEL DỮ LIỆU CỤC BỘ)
# ==============================================================================

class ForgotPasswordRequest(BaseModel):
    email: str

class UserUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
    brand_name: Optional[str] = None
    keywords: Optional[List[str]] = None

class AdminUserUpdate(BaseModel):
    """Model dành cho Admin cập nhật user"""
    role: Optional[str] = None
    is_active: Optional[bool] = None
    brand_name: Optional[str] = None
    keywords: Optional[List[str]] = None
    active_sources: Optional[dict] = None
    password: Optional[str] = None
    crawl_frequency: Optional[int] = None

class AnalyzeRequest(BaseModel):
    url: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)

class PostUpdate(BaseModel):
    sentiment: Optional[str] = None
    is_spam: Optional[bool] = None

class KeywordRequest(BaseModel):
    keyword: str

# ==============================================================================
# 3. HELPER FUNCTIONS (HÀM TIỆN ÍCH)
# ==============================================================================

def generate_strong_password(length=12):
    """Tạo mật khẩu ngẫu nhiên an toàn"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return password

def get_youtube_transcript(video_id):
    """Lấy phụ đề YouTube (Ưu tiên Tiếng Việt -> Anh -> Auto)"""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            transcript = transcript_list.find_manually_created_transcript(['vi'])
        except:
            try:
                transcript = transcript_list.find_generated_transcript(['vi'])
            except:
                try:
                    transcript = transcript_list.find_manually_created_transcript(['en'])
                except:
                    # Fallback lấy bất kỳ cái nào
                    transcript = transcript_list.find_generated_transcript(['en'])
        
        full_text = " ".join([t['text'] for t in transcript.fetch()])
        return full_text
    except Exception:
        return ""

def gemini_summarize(text, max_words=300):
    """Dùng Gemini để tóm tắt nội dung dài"""
    try:
        prompt = f"""Hãy tóm tắt nội dung văn bản sau đây thành khoảng {max_words} từ bằng Tiếng Việt. 
        Tập trung vào các ý chính, quan điểm và thái độ của bài viết/video.
        
        Nội dung:
        {text[:10000]} # Giới hạn token
        
        Tóm tắt:"""
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return text[:500] + "..." # Fallback nếu lỗi AI

def calculate_marketing_score(sentiment_score, views, likes, comments, shares=0, platform="generic", published_at=None):
    """
    Tính điểm Marketing Score (Impact) v2.0
    Kết hợp Engagement, View Impact và Time Decay
    """
    # 1. Weighted Engagement
    if platform == "youtube":
        w_like = 2; w_comment = 5; w_share = 0
    else:
        w_like = 1; w_comment = 2; w_share = 4

    weighted_engagement = (likes * w_like) + (comments * w_comment) + (shares * w_share)
    
    # 2. View Impact (Log scale reward)
    if views > 0:
        base_log = math.log10(views + 1)
        reach_impact = math.pow(base_log, 1.3) 
    else:
        reach_impact = 0
        
    # 3. Raw Score
    smoothing_factor = 300 if platform == "youtube" else 500
    raw_impact = reach_impact * (1 + (weighted_engagement / smoothing_factor))
    
    # 4. Sentiment Magnitude
    sentiment_magnitude = abs(sentiment_score)
    if sentiment_magnitude < 0.2: sentiment_magnitude = 0.5 
    
    score_before_decay = raw_impact * sentiment_magnitude
    
    # 5. Time Decay (Phạt nội dung cũ)
    decay_factor = 1.0
    if published_at:
        try:
            if isinstance(published_at, str):
                for fmt in ('%Y%m%d', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ'):
                    try:
                        published_at = datetime.strptime(published_at, fmt)
                        break
                    except ValueError: pass
            
            if isinstance(published_at, datetime):
                if published_at.tzinfo: published_at = published_at.replace(tzinfo=None)
                age_days = (datetime.now() - published_at).days
                if age_days < 0: age_days = 0
                decay_factor = math.pow(0.1, age_days / 30.0)
        except Exception: pass

    final_raw_score = score_before_decay * decay_factor

    # 6. Chuẩn hóa thang 10
    normalization_factor = 25 if platform == "youtube" else 20
    normalized_score = 10 * (1 - math.exp(-final_raw_score / normalization_factor))
    
    return round(normalized_score, 1)

# ==============================================================================
# 4. LIFECYCLE EVENTS (STARTUP / SHUTDOWN)
# ==============================================================================

@app.on_event("startup")
async def startup_db_client():
    """Chạy khi server bắt đầu: Kết nối DB và khởi động Scheduler"""
    await db_manager.connect()
    try:
        scheduler.start()
        if log_activity:
            await log_activity("INFO", "SYSTEM", "SCHEDULER", "Đã khởi động bộ lập lịch tự động")
    except Exception as e:
        print(f"Lỗi khởi động Scheduler: {e}")

    if log_activity:
        await log_activity("INFO", "SYSTEM", "STARTUP", "Server Backend đã khởi động")

@app.on_event("shutdown")
async def shutdown_db_client():
    """Chạy khi server tắt: Ngắt DB và dừng Scheduler"""
    try:
        scheduler.stop()
    except Exception as e:
        print(f"Lỗi tắt Scheduler: {e}")
    await db_manager.disconnect()

# ==============================================================================
# 5. AUTHENTICATION API (ĐĂNG NHẬP / QUÊN MẬT KHẨU)
# ==============================================================================

@app.post("/token", response_model=TokenResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """API Đăng nhập lấy Token"""
    user = await db_manager.get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user["password"]):
        if log_activity:
            await log_activity("WARNING", form_data.username, "LOGIN_FAIL", "Sai mật khẩu hoặc email")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=300) # 5 tiếng
    access_token = create_access_token(
        data={"sub": user["email"], "role": user.get("role", "user")}, 
        expires_delta=access_token_expires
    )
    
    if log_activity:
        await log_activity("INFO", user["email"], "LOGIN", "Đăng nhập thành công")
    
    real_username = user.get("username", user["email"].split("@")[0])

    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "role": user.get("role", "user"),
        "username": real_username
    }

@app.post("/api/auth/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, background_tasks: BackgroundTasks):
    """API Quên mật khẩu: Reset và gửi mail"""
    user = await db_manager.get_user_by_email(req.email)
    if not user:
        raise HTTPException(status_code=404, detail="Email không tồn tại trong hệ thống")

    alphabet = string.ascii_letters + string.digits
    new_raw_password = ''.join(secrets.choice(alphabet) for i in range(8))
    hashed_password = get_password_hash(new_raw_password)

    await db_manager.database["users"].update_one(
        {"email": req.email},
        {"$set": {"password": hashed_password}}
    )

    if send_reset_password_email:
        background_tasks.add_task(send_reset_password_email, req.email, new_raw_password)

    return {"message": "Mật khẩu mới đã được gửi vào email của bạn."}

# ==============================================================================
# 6. USER MANAGEMENT API (QUẢN LÝ NGƯỜI DÙNG)
# ==============================================================================

@app.get("/api/users")
async def get_users(current_user: dict = Depends(get_current_user)):
    """[Admin] Lấy danh sách toàn bộ user"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    users = await db_manager.database["users"].find().to_list(length=100)
    for u in users:
        u["id"] = str(u["_id"])
        del u["_id"]
        del u["password"]
    return users

@app.post("/api/users/create", response_model=UserResponse)
async def create_user(
    user_data: UserCreate, 
    background_tasks: BackgroundTasks, 
    current_user: dict = Depends(get_current_user)
):
    """[Admin] Tạo user mới"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Không có quyền thực hiện")

    existing_user = await db_manager.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email đã tồn tại")

    raw_password = generate_strong_password(12)
    hashed_pass = get_password_hash(raw_password)
    
    final_keywords = user_data.keywords if user_data.role == "user" else []
    final_brand = user_data.brand_name if user_data.role == "user" else None

    new_user = {
        "email": user_data.email,
        "username": user_data.username,
        "password": hashed_pass,
        "role": user_data.role,
        "keywords": final_keywords,
        "brand_name": final_brand,
        "active_sources": user_data.active_sources if hasattr(user_data, 'active_sources') else {"youtube": True, "news": True},
        "crawl_frequency": user_data.crawl_frequency if hasattr(user_data, 'crawl_frequency') else 720,
        "is_active": True,
        "created_at": datetime.now()
    }
    
    user_id = await db_manager.create_user(new_user)
    
    # Gửi email thông báo
    if send_new_account_email:
        background_tasks.add_task(
            send_new_account_email, 
            to_email=user_data.email, 
            username=user_data.username, 
            password=raw_password 
        )

    # Kích hoạt thu thập ngay
    if user_data.role == "user" and final_keywords and collect_data_for_user:
        background_tasks.add_task(
            collect_data_for_user, 
            keywords=final_keywords, 
            brand_name=final_brand,
            active_sources=new_user["active_sources"],
            user_id=str(user_id),
            user_email=new_user["email"]
        )

    if log_activity:
        await log_activity("SUCCESS", current_user["email"], "CREATE_USER", f"Tạo user: {user_data.email}")

    return {**new_user, "id": str(user_id)}

@app.put("/api/users/{user_id}")
async def update_user_by_admin(
    user_id: str, 
    user_data: AdminUserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """[Admin] Cập nhật thông tin User (bao gồm reset pass, cài đặt crawl)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Bạn không có quyền này")

    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="ID người dùng không hợp lệ")

    update_fields = {k: v for k, v in user_data.dict().items() if v is not None}

    if "password" in update_fields:
        if len(update_fields["password"]) < 6:
            raise HTTPException(status_code=400, detail="Mật khẩu phải từ 6 ký tự")
        update_fields["password"] = get_password_hash(update_fields["password"])
    
    if not update_fields:
        return {"message": "Không có thông tin nào thay đổi"}

    update_fields["updated_at"] = datetime.now()

    result = await db_manager.database["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_fields}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy User")

    if log_activity:
        await log_activity("INFO", current_user["email"], "UPDATE_USER", f"Admin cập nhật user {user_id}")
        
    return {"message": "Cập nhật thành công"}

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """[Admin] Xóa user"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    try:
        res = await db_manager.database["users"].delete_one({"_id": ObjectId(user_id)})
        if res.deleted_count == 1:
            if log_activity:
                await log_activity("WARNING", current_user["email"], "DELETE_USER", f"Xóa user ID: {user_id}")
            return {"message": "Đã xóa thành công"}
        raise HTTPException(status_code=404, detail="User not found")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")

@app.get("/api/users/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """[User] Lấy thông tin bản thân"""
    keywords_list = current_user.get("keywords", [])
    keywords_str = ", ".join(keywords_list) if isinstance(keywords_list, list) else str(keywords_list)

    return {
        "email": current_user["email"],
        "username": current_user.get("username", ""),
        "role": current_user.get("role", "user"),
        "brand_name": current_user.get("brand_name", ""),
        "keywords": keywords_str,
        "active_sources": current_user.get("active_sources", {"youtube": True, "news": True})
    }

@app.put("/api/users/settings")
async def update_user_settings(settings_data: UserSettingsUpdate, current_user: dict = Depends(get_current_user)):
    """[User] Cập nhật cài đặt cá nhân"""
    raw_keywords = settings_data.keywords
    keywords_list = [k.strip() for k in raw_keywords.split(",") if k.strip()]
    
    update_data = {
        "brand_name": settings_data.brand_name,
        "keywords": keywords_list,
        "active_sources": settings_data.active_sources,
        "updated_at": datetime.now()
    }
    
    await db_manager.database["users"].update_one(
        {"email": current_user["email"]},
        {"$set": update_data}
    )
    if log_activity:
        log_msg = f"Đổi Brand: {settings_data.brand_name} | Keywords: {len(keywords_list)} từ"
        await log_activity("INFO", current_user["email"], "UPDATE_SETTINGS", log_msg)
    return {"message": "Cập nhật thành công", "data": update_data}

@app.post("/api/change-password")
async def change_password(
    request: ChangePasswordRequest, 
    current_user: dict = Depends(get_current_user)
):
    """[User/Admin] Tự đổi mật khẩu bản thân"""
    if not verify_password(request.current_password, current_user["password"]):
        raise HTTPException(status_code=400, detail="Mật khẩu cũ không chính xác")
    
    new_hashed_password = get_password_hash(request.new_password)
    
    await db_manager.database["users"].update_one(
        {"_id": current_user["_id"]},
        {"$set": {"password": new_hashed_password}}
    )
    
    if log_activity:
        await log_activity("INFO", current_user["email"], "CHANGE_PASS", "Đổi mật khẩu thành công")

    return {"message": "Đổi mật khẩu thành công"}

# ==============================================================================
# 7. SYSTEM & CONFIG API (HỆ THỐNG)
# ==============================================================================

@app.get("/api/logs")
async def get_system_logs(limit: int = 50, current_user: dict = Depends(get_current_user)):
    """Lấy nhật ký hệ thống"""
    cursor = db_manager.database["system_logs"].find().sort("created_at", -1).limit(limit)
    logs = await cursor.to_list(length=limit)
    for log in logs:
        log["id"] = str(log["_id"])
        del log["_id"]
    return logs

@app.get("/api/system/config")
async def get_system_config():
    """Lấy cấu hình hệ thống (Crawl delay, API keys...)"""
    config = await db_manager.database["system_config"].find_one()
    if not config:
        return {
            "crawl_delay_news": 15, "crawl_delay_social": 30, 
            "active_sources": {"youtube": True, "news": True},
            "blacklist_keywords": [], "api_keys": []
        }
    config["id"] = str(config["_id"])
    del config["_id"]
    return config

@app.put("/api/system/config")
async def update_system_config(config_data: SystemConfiguration):
    """Cập nhật cấu hình hệ thống"""
    update_data = config_data.dict(exclude={"id"}, exclude_unset=True)
    update_data["updated_at"] = datetime.now()
    
    existing = await db_manager.database["system_config"].find_one()
    if existing:
        await db_manager.database["system_config"].update_one(
            {"_id": existing["_id"]}, {"$set": update_data}
        )
    else:
        await db_manager.database["system_config"].insert_one(update_data)
    return {"message": "Saved"}

@app.post("/api/collect/run")
async def trigger_collection(background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    """Kích hoạt thu thập dữ liệu thủ công (Manual Trigger)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
        
    if main_orchestrator:
        background_tasks.add_task(main_orchestrator)
        if log_activity: await log_activity("INFO", current_user["email"], "CRAWL", "Kích hoạt thu thập thủ công")
        return {"status": "accepted", "message": "Đã kích hoạt thu thập"}
    else:
        return {"status": "error", "message": "Chưa cấu hình Collector"}

@app.get("/api/notifications")
async def get_notifications(current_user: dict = Depends(get_current_user)):
    """Lấy các thông báo (Cảnh báo khủng hoảng...)"""
    query = {"user_id": str(current_user["_id"]), "is_read": False}
    cursor = db_manager.database["notifications"].find(query).sort("created_at", -1)
    notifs = await cursor.to_list(length=10)
    
    results = []
    for n in notifs:
        n["id"] = str(n["_id"])
        del n["_id"]
        results.append(n)
    return results

@app.put("/api/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: str, current_user: dict = Depends(get_current_user)):
    """Đánh dấu đã đọc thông báo"""
    await db_manager.database["notifications"].update_one(
        {"_id": ObjectId(notif_id), "user_id": str(current_user["_id"])},
        {"$set": {"is_read": True}}
    )
    return {"message": "Marked as read"}

# ==============================================================================
# 8. POSTS & CONTENT API (BÀI VIẾT & DỮ LIỆU)
# ==============================================================================

@app.get("/api/dashboard/data")
async def get_dashboard_data(current_user: dict = Depends(get_current_user)):
    """Lấy dữ liệu hiển thị lên Dashboard (phân chia theo Youtube/News)"""
    filter_query = {}
    
    # Nếu là User thường, lọc theo Keywords/Brand của họ
    if current_user.get("role") != "admin":
        keywords = current_user.get("keywords", [])
        brand = current_user.get("brand_name", "")
        
        conditions = []
        if brand:
            conditions.append({"brand_name": brand})
            conditions.append({"title": {"$regex": brand, "$options": "i"}})
        
        if keywords:
            clean_keywords = [k.strip() for k in keywords if k.strip()]
            if clean_keywords:
                keyword_regex = "|".join(clean_keywords)
                conditions.append({"title": {"$regex": keyword_regex, "$options": "i"}})
                conditions.append({"content": {"$regex": keyword_regex, "$options": "i"}})
        
        if conditions:
            filter_query = {"$or": conditions}
        else:
            return {"news": [], "youtube": []}

    try:
        news_cursor = db_manager.database["posts"].find({
            "platform": "news", **filter_query
        }).sort("published_at", -1).limit(50)
        news_data = await news_cursor.to_list(length=50)
        
        yt_cursor = db_manager.database["posts"].find({
            "platform": "youtube", **filter_query
        }).sort("published_at", -1).limit(50)
        yt_data = await yt_cursor.to_list(length=50)
    except Exception as e:
        print(f"Lỗi query dashboard: {e}")
        return {"news": [], "youtube": []}

    def format_data(items):
        formatted = []
        for item in items:
            item["id"] = str(item["_id"])
            del item["_id"]
            formatted.append(item)
        return formatted

    return {
        "news": format_data(news_data),
        "youtube": format_data(yt_data)
    }

@app.post("/api/analyze-url")
async def analyze_url(req: AnalyzeRequest, current_user: dict = Depends(get_current_user)):
    """Phân tích nhanh 1 đường link (URL) bất kỳ"""
    url = req.url.strip()
    user_keywords = current_user.get("keywords", [])
    keywords_list = [str(k).strip().lower() for k in user_keywords if k] if user_keywords else []

    is_youtube = "youtube.com" in url or "youtu.be" in url
    is_news = url.startswith("http") and not ("facebook.com" in url or "tiktok.com" in url)
    
    if not (is_youtube or is_news):
        raise HTTPException(status_code=400, detail="Hiện tại chỉ hỗ trợ link YouTube hoặc Báo chí.")

    # Thu thập dữ liệu
    title = ""; full_content = ""; platform = "news"
    views = 0; likes = 0; comments = 0; shares = 0
    published_at = datetime.now()

    try:
        if is_youtube:
            platform = "youtube"
            ydl_opts = {'quiet': True, 'skip_download': True, 'ignoreerrors': True, 'extract_flat': True}
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info: raise Exception("Không tìm thấy thông tin video")
                title = info.get('title', ''); video_id = info.get('id')
                views = info.get('view_count', 0) or 0
                likes = info.get('like_count', 0) or 0
                comments = info.get('comment_count', 0) or 0
                shares = info.get('repost_count', 0) or 0
                transcript = get_youtube_transcript(video_id)
                full_content = transcript if transcript else info.get('description', '')
        else:
            platform = "news"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            resp = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            title = soup.title.string.strip() if soup.title else url
            paragraphs = soup.find_all('p')
            full_content = " ".join([p.get_text() for p in paragraphs])
            views = 1000 # Giả lập

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lỗi khi đọc đường dẫn: {str(e)}")

    if len(full_content) < 50:
        raise HTTPException(status_code=400, detail="Nội dung quá ngắn.")

    # Phân tích AI
    summary = gemini_summarize(full_content)
    sentiment_score = sentiment_model.predict(summary)
    
    sentiment_label = "NEUTRAL"
    if sentiment_score > 0.15: sentiment_label = "POSITIVE"
    elif sentiment_score < -0.15: sentiment_label = "NEGATIVE"
    
    marketing_score = calculate_marketing_score(
        sentiment_score=sentiment_score, views=views, likes=likes, 
        comments=comments, shares=shares, platform=platform
    )

    # Kiểm tra khớp từ khóa & Lưu DB
    has_keyword = False; matched_keyword = ""
    content_check = (title + " " + full_content).lower()
    
    if keywords_list:
        for kw in keywords_list:
            if kw in content_check:
                has_keyword = True; matched_keyword = kw; break

    if has_keyword:
        post_doc = {
            "platform": platform, "source_url": url, "source_name": "Quick Analysis",
            "title": title, "content": summary, "original_content_snippet": full_content[:2000],
            "sentiment": sentiment_label, "sentiment_score": float(sentiment_score),
            "marketing_score": float(marketing_score),
            "views_count": views, "likes_count": likes, "comments_count": comments, "shares_count": shares,
            "published_at": published_at, "created_at": datetime.now(),
            "keywords_matched": [matched_keyword], "is_manual_analysis": True,
            "user_id": str(current_user["_id"])
        }
        await db_manager.database["posts"].insert_one(post_doc)
        if log_activity:
            await log_activity("INFO", current_user["email"], "QUICK_ANALYSIS", f"Phân tích: {url}")

    return {
        "title": title, "platform": platform, "content_snippet": summary,
        "sentiment": sentiment_label, "sentiment_score": round(float(sentiment_score), 3),
        "marketing_score": round(float(marketing_score), 1),
        "has_keyword": has_keyword, "matched_keyword": matched_keyword, "saved": has_keyword
    }

@app.get("/api/posts/moderation")
async def get_posts_for_moderation(
    page: int = 1, limit: int = 20, platform: str = "all", 
    sentiment: str = "all", search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """[Admin] Lấy danh sách bài viết để kiểm duyệt"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")

    query = {}
    if platform != "all": query["platform"] = platform
    if sentiment != "all": query["sentiment"] = sentiment
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"content": {"$regex": search, "$options": "i"}}
        ]

    skip = (page - 1) * limit
    cursor = db_manager.database["posts"].find(query).sort("published_at", -1).skip(skip).limit(limit)
    posts = await cursor.to_list(length=limit)
    total = await db_manager.database["posts"].count_documents(query)

    formatted_posts = []
    for p in posts:
        p["id"] = str(p["_id"])
        del p["_id"]
        formatted_posts.append(p)

    return {"data": formatted_posts, "total": total, "page": page, "total_pages": (total // limit) + 1}

@app.put("/api/posts/{post_id}")
async def update_post(
    post_id: str, 
    update_data: PostUpdate,
    current_user: dict = Depends(get_current_user)
):
    """[Admin] Cập nhật nhãn bài viết"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")

    if not ObjectId.is_valid(post_id):
        raise HTTPException(status_code=400, detail="Invalid ID")

    fields = {k: v for k, v in update_data.dict().items() if v is not None}
    if "sentiment" in fields: fields["confidence_score"] = 1.0

    await db_manager.database["posts"].update_one(
        {"_id": ObjectId(post_id)}, {"$set": fields}
    )
    return {"message": "Cập nhật thành công"}

@app.get("/api/posts/detail/{post_id}")
async def get_post_detail(post_id: str, current_user: dict = Depends(get_current_user)):
    """Xem chi tiết một bài viết"""
    if not ObjectId.is_valid(post_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")
        
    post = await db_manager.database["posts"].find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài viết")
        
    post["id"] = str(post["_id"])
    del post["_id"]
    return post

@app.get("/api/posts/export")
async def export_posts(
    platform: str = "all", sentiment: str = "all", search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Xuất dữ liệu ra file CSV (Streaming)"""
    query = {}
    if current_user.get("role") != "admin":
        keywords = current_user.get("keywords", [])
        brand = current_user.get("brand_name", "")
        conditions = []
        if brand: conditions.append({"title": {"$regex": brand, "$options": "i"}})
        if keywords:
            keyword_regex = "|".join([k.strip() for k in keywords if k.strip()])
            if keyword_regex:
                conditions.append({"title": {"$regex": keyword_regex, "$options": "i"}})
                conditions.append({"content": {"$regex": keyword_regex, "$options": "i"}})
        
        query["$or"] = conditions if conditions else {"_id": -1}

    if platform != "all": query["platform"] = platform
    if sentiment != "all": query["sentiment"] = sentiment
    if search:
        query["$or"] = [{"title": {"$regex": search, "$options": "i"}}, {"content": {"$regex": search, "$options": "i"}}]

    async def iter_csv():
        output = io.StringIO()
        writer = csv.writer(output)
        output.write('\ufeff') # BOM for Excel Vietnamese
        writer.writerow(["ID", "Nền tảng", "Tiêu đề", "URL Gốc", "Ngày đăng", "Cảm xúc", "Điểm MKT", "Lượt xem", "Lượt thích", "Bình luận"])
        yield output.getvalue(); output.seek(0); output.truncate(0)

        cursor = db_manager.database["posts"].find(query).sort("published_at", -1)
        async for p in cursor:
            pub_date = p.get("published_at", "")
            if isinstance(pub_date, datetime): pub_date = pub_date.strftime("%d/%m/%Y %H:%M")

            writer.writerow([
                str(p.get("_id", "")), p.get("platform", "").upper(), p.get("title", "No Title"),
                p.get("source_url", ""), pub_date, p.get("sentiment", "NEUTRAL"),
                p.get("marketing_score", 0), p.get("views_count", 0), p.get("likes_count", 0), p.get("comments_count", 0)
            ])
            yield output.getvalue(); output.seek(0); output.truncate(0)

    filename = f"Veda_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return StreamingResponse(iter_csv(), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={filename}"})

# ==============================================================================
# 9. ANALYTICS & KEYWORDS API (THỐNG KÊ & TỪ KHÓA)
# ==============================================================================

@app.get("/api/stats/sentiment-chart")
async def get_sentiment_chart(period: str = "week", current_user: dict = Depends(get_current_user)):
    """Lấy dữ liệu biểu đồ cảm xúc theo thời gian"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30 if period == "month" else 7)

    pipeline = [
        {"$match": {"created_at": {"$gte": start_date, "$lte": end_date}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "positive": {"$sum": {"$cond": [{"$eq": ["$sentiment", "POSITIVE"]}, 1, 0]}},
            "negative": {"$sum": {"$cond": [{"$eq": ["$sentiment", "NEGATIVE"]}, 1, 0]}},
            "neutral": {"$sum": {"$cond": [{"$eq": ["$sentiment", "NEUTRAL"]}, 1, 0]}}
        }},
        {"$sort": {"_id": 1}}
    ]

    stats = await db_manager.database["posts"].aggregate(pipeline).to_list(length=31)
    return [{"date": item["_id"], "positive": item["positive"], "negative": item["negative"], "neutral": item["neutral"]} for item in stats]

@app.post("/api/keywords")
async def add_keyword(req: KeywordRequest, current_user: dict = Depends(get_current_user)):
    """Thêm từ khóa theo dõi"""
    await db_manager.database["users"].update_one(
        {"_id": current_user["_id"]},
        {"$addToSet": {"keywords": req.keyword}}
    )
    return {"message": f"Đã thêm từ khóa: {req.keyword}"}

@app.delete("/api/keywords/{keyword}")
async def remove_keyword(keyword: str, current_user: dict = Depends(get_current_user)):
    """Xóa từ khóa theo dõi"""
    await db_manager.database["users"].update_one(
        {"_id": current_user["_id"]},
        {"$pull": {"keywords": keyword}}
    )
    return {"message": f"Đã xóa từ khóa: {keyword}"}
# backend/api/main.py

# ... (các import hiện có)

@app.delete("/api/posts/{post_id}")
async def delete_post(post_id: str, current_user: dict = Depends(get_current_user)):
    """[Admin] Xóa vĩnh viễn một bài viết"""
    # 1. Kiểm tra quyền Admin
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Bạn không có quyền thực hiện thao tác này")

    # 2. Kiểm tra ID hợp lệ
    if not ObjectId.is_valid(post_id):
        raise HTTPException(status_code=400, detail="ID bài viết không hợp lệ")

    # 3. Thực hiện xóa
    result = await db_manager.database["posts"].delete_one({"_id": ObjectId(post_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài viết để xóa")
        
    # Ghi log hoạt động
    if log_activity:
        await log_activity("WARNING", current_user["email"], "DELETE_POST", f"Đã xóa bài viết ID: {post_id}")

    return {"message": "Đã xóa bài viết thành công"}
# ==============================================================================
# 10. MAIN ENTRY
# ==============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)