from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import List, Optional
import os
import sys
import traceback
from bson import ObjectId
import math
import requests
from bs4 import BeautifulSoup
import re
import google.generativeai as genai
import secrets
import string
# Fix đường dẫn import để Python tìm thấy module 'backend'
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import các module trong dự án
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
# Import Service Email & Collector
try:
    from backend.services.email_service import send_new_account_email
except ImportError:
    send_new_account_email = None

try:
    from backend.collectors.run_collector import collect_data_for_user, main_orchestrator
except ImportError:
    collect_data_for_user = None
    main_orchestrator = None
# Import thư viện thu thập dữ liệu chuyên sâu
from yt_dlp import YoutubeDL
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
# --- KHỞI TẠO APP ---
app = FastAPI(title=settings.PROJECT_NAME)

# --- CẤU HÌNH CORS ---
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
# Khởi tạo AI Model
sentiment_model = CustomSentimentModel()
genai.configure(api_key=settings.GEMINI_API_KEYS[0] if settings.GEMINI_API_KEYS else "")
gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)

# --- HELPER FUNCTIONS (Tái sử dụng logic từ Collectors) ---
def generate_strong_password(length=12):
    """Tạo mật khẩu ngẫu nhiên an toàn gồm chữ hoa, thường, số và ký tự đặc biệt"""
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

import math

def calculate_marketing_score(sentiment_score, views, likes, comments, shares=0, platform="generic", published_at=None):
    """
    Tính điểm Marketing Score (Impact) v2.0
    - Phạt nặng video cũ (Exponential Decay)
    - Thưởng lớn cho video Viral (Non-linear View Impact)
    """
    
    # --- 1. Weighted Engagement (Tương tác có trọng số) ---
    if platform == "youtube":
        w_like = 2      
        w_comment = 5   
        w_share = 0     
    else:
        w_like = 1
        w_comment = 2
        w_share = 4

    weighted_engagement = (likes * w_like) + (comments * w_comment) + (shares * w_share)
    
    # --- 2. View Impact (Sức mạnh lan tỏa - Cải tiến) ---
    # Thay vì log10 thuần (tăng chậm), ta dùng log10^1.3 để thưởng cho video view khủng
    # Ví dụ: 10k view = 6 điểm; 1M view = 10.2 điểm (Gấp đôi điểm thay vì chỉ nhích nhẹ)
    if views > 0:
        base_log = math.log10(views + 1)
        reach_impact = math.pow(base_log, 1.3) 
    else:
        reach_impact = 0
        
    # --- 3. Raw Score ---
    smoothing_factor = 300 if platform == "youtube" else 500
    raw_impact = reach_impact * (1 + (weighted_engagement / smoothing_factor))
    
    # --- 4. Sentiment Magnitude ---
    sentiment_magnitude = abs(sentiment_score)
    if sentiment_magnitude < 0.2: sentiment_magnitude = 0.5 
    
    score_before_decay = raw_impact * sentiment_magnitude
    
    # --- 5. Time Decay (Phạt thời gian - Cực mạnh) ---
    # Target: 10% score remaining at 30 days.
    # Formula: 0.1 ^ (age_days / 30)
    decay_factor = 1.0
    if published_at:
        try:
            # Handle string input
            if isinstance(published_at, str):
                # Try simple formats first
                for fmt in ('%Y%m%d', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ'):
                    try:
                        published_at = datetime.strptime(published_at, fmt)
                        break
                    except ValueError:
                        pass
            
            if isinstance(published_at, datetime):
                # Make timezone-naive for subtraction
                if published_at.tzinfo:
                    published_at = published_at.replace(tzinfo=None)
                
                age_days = (datetime.now() - published_at).days
                if age_days < 0: age_days = 0
                
                # Geometric Decay Logic
                decay_factor = math.pow(0.1, age_days / 30.0)
                
        except Exception as e:
            print(f"Decay calc error: {e}")
            pass

    final_raw_score = score_before_decay * decay_factor

    # --- 6. Chuẩn hóa thang 10 ---
    normalization_factor = 25 if platform == "youtube" else 20
    normalized_score = 10 * (1 - math.exp(-final_raw_score / normalization_factor))
    
    return round(normalized_score, 1)

class ForgotPasswordRequest(BaseModel):
    email: str
class UserUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
    brand_name: Optional[str] = None
    keywords: Optional[List[str]] = None
class AnalyzeRequest(BaseModel):
    url: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)
# --- SỰ KIỆN KHỞI ĐỘNG ---
@app.on_event("startup")
async def startup_db_client():
    await db_manager.connect()
    
    # [QUAN TRỌNG] Bật bộ đếm giờ (Scheduler)
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
    # [QUAN TRỌNG] Tắt bộ đếm giờ khi server tắt
    try:
        scheduler.stop()
    except Exception as e:
        print(f"Lỗi tắt Scheduler: {e}")
        
    # --- ĐÃ SỬA LỖI TẠI ĐÂY (Bỏ ngoặc đơn thừa) ---
    await db_manager.disconnect()

# ==================================================================
# CÁC API ENDPOINTS
# ==================================================================

# 1. ĐĂNG NHẬP (SỬ DỤNG /token ĐỂ KHỚP VỚI FRONTEND)
@app.post("/token", response_model=TokenResponse) # Sửa response_model thành TokenResponse
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db_manager.get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user["password"]):
        if log_activity:
            await log_activity("WARNING", form_data.username, "LOGIN_FAIL", "Sai mật khẩu hoặc email")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Tạo token
    access_token_expires = timedelta(minutes=300) # 5 tiếng
    access_token = create_access_token(
        data={"sub": user["email"], "role": user.get("role", "user")}, 
        expires_delta=access_token_expires
    )
    
    if log_activity:
        await log_activity("INFO", user["email"], "LOGIN", "Đăng nhập thành công")
    
    # [THÊM] Trả về username từ DB, nếu không có thì lấy phần đầu email
    real_username = user.get("username", user["email"].split("@")[0])

    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "role": user.get("role", "user"),
        "username": real_username # [QUAN TRỌNG] Trả về username
    }

# 2. TẠO USER MỚI (ĐẦY ĐỦ TÍNH NĂNG)
@app.post("/api/users/create", response_model=UserResponse)
async def create_user(
    user_data: UserCreate, 
    background_tasks: BackgroundTasks, 
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Không có quyền thực hiện")

    existing_user = await db_manager.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email đã tồn tại")

    # [THAY ĐỔI] Tự động sinh mật khẩu ngẫu nhiên
    # Kể cả user_data.password có dữ liệu hay không, ta cũng ghi đè bằng mật khẩu mới cho an toàn
    raw_password = generate_strong_password(12)
    
    # Hash mật khẩu để lưu vào DB
    hashed_pass = get_password_hash(raw_password)
    
    # Xử lý logic user/admin
    final_keywords = user_data.keywords if user_data.role == "user" else []
    final_brand = user_data.brand_name if user_data.role == "user" else None

    new_user = {
        "email": user_data.email,
        "username": user_data.username,
        "password": hashed_pass, # Lưu bản đã mã hóa
        "role": user_data.role,
        "keywords": final_keywords,
        "brand_name": final_brand,
        "is_active": True,
        "created_at": datetime.now()
    }
    
    user_id = await db_manager.create_user(new_user)
    
    # --- KÍCH HOẠT TÁC VỤ NGẦM ---
    
    # 1. Gửi email thông báo (QUAN TRỌNG: Gửi raw_password chưa hash để user đọc được)
    if send_new_account_email:
        background_tasks.add_task(
            send_new_account_email, 
            to_email=user_data.email, 
            username=user_data.username, 
            password=raw_password  # Gửi mật khẩu gốc qua mail
        )
        # Log việc gửi mail
        if log_activity:
            await log_activity("INFO", "SYSTEM", "SEND_MAIL", f"Đã gửi mật khẩu tới {user_data.email}")

    # 2. Kích hoạt thu thập dữ liệu ngay lập tức
    if user_data.role == "user" and final_keywords and collect_data_for_user:
        background_tasks.add_task(
            collect_data_for_user, 
            keywords=final_keywords, 
            brand_name=final_brand,
            active_sources={"youtube": True, "news": True}, # [THÊM] Truyền cấu hình mặc định
            user_id=str(user_id),
            user_email=new_user["email"]
        )
        if log_activity:
            await log_activity("INFO", "SYSTEM", "AUTO_CRAWL", f"Kích hoạt crawl cho {user_data.email}")

    if log_activity:
        await log_activity("SUCCESS", current_user["email"], "CREATE_USER", f"Tạo user: {user_data.email}")

    # Trả về thông tin user (Lưu ý: Không trả về mật khẩu trong response)
    return {**new_user, "id": str(user_id)}
@app.get("/api/notifications")
async def get_notifications(current_user: dict = Depends(get_current_user)):
    """Lấy các thông báo chưa đọc"""
    query = {"user_id": str(current_user["_id"]), "is_read": False}
    cursor = db_manager.database["notifications"].find(query).sort("created_at", -1)
    notifs = await cursor.to_list(length=10)
    
    # Format dữ liệu
    results = []
    for n in notifs:
        n["id"] = str(n["_id"])
        del n["_id"]
        results.append(n)
        
    return results

@app.put("/api/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: str, current_user: dict = Depends(get_current_user)):
    """Đánh dấu đã đọc"""
    await db_manager.database["notifications"].update_one(
        {"_id": ObjectId(notif_id), "user_id": str(current_user["_id"])},
        {"$set": {"is_read": True}}
    )
    return {"message": "Marked as read"}
# 3. LẤY DANH SÁCH USER
@app.get("/api/users")
async def get_users(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    users = await db_manager.database["users"].find().to_list(length=100)
    for u in users:
        u["id"] = str(u["_id"])
        del u["_id"]
        del u["password"]
    return users

# 4. XÓA USER
@app.delete("/api/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    from bson import ObjectId
    try:
        res = await db_manager.database["users"].delete_one({"_id": ObjectId(user_id)})
        if res.deleted_count == 1:
            if log_activity:
                await log_activity("WARNING", current_user["email"], "DELETE_USER", f"Xóa user ID: {user_id}")
            return {"message": "Đã xóa thành công"}
        raise HTTPException(status_code=404, detail="User not found")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")

# 5. LẤY LOG HỆ THỐNG
@app.get("/api/logs")
async def get_system_logs(limit: int = 50, current_user: dict = Depends(get_current_user)):
    cursor = db_manager.database["system_logs"].find().sort("created_at", -1).limit(limit)
    logs = await cursor.to_list(length=limit)
    for log in logs:
        log["id"] = str(log["_id"])
        del log["_id"]
    return logs

# 6. CẤU HÌNH HỆ THỐNG
@app.get("/api/system/config")
async def get_system_config():
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

# 7. ĐỔI MẬT KHẨU
@app.post("/api/change-password")
async def change_password(
    request: ChangePasswordRequest, 
    current_user: dict = Depends(get_current_user)
):
    # Sửa old_password -> current_password
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

# 8. KÍCH HOẠT CRAWL THỦ CÔNG
@app.post("/api/collect/run")
async def trigger_collection(background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
        
    if main_orchestrator:
        background_tasks.add_task(main_orchestrator)
        if log_activity: await log_activity("INFO", current_user["email"], "CRAWL", "Kích hoạt thu thập thủ công")
        return {"status": "accepted", "message": "Đã kích hoạt thu thập"}
    else:
        return {"status": "error", "message": "Chưa cấu hình Collector"}

# --- API 1: LẤY DANH SÁCH BÀI VIẾT (CÓ PHÂN TRANG & LỌC) ---
@app.get("/api/posts/moderation")
async def get_posts_for_moderation(
    page: int = 1,
    limit: int = 20,
    platform: str = "all",
    sentiment: str = "all",
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")

    # Xây dựng query
    query = {}
    if platform != "all":
        query["platform"] = platform
    if sentiment != "all":
        query["sentiment"] = sentiment
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"content": {"$regex": search, "$options": "i"}}
        ]

    # Tính toán phân trang
    skip = (page - 1) * limit

    # Query DB
    cursor = db_manager.database["posts"].find(query).sort("published_at", -1).skip(skip).limit(limit)
    posts = await cursor.to_list(length=limit)
    
    # Đếm tổng số bài (để làm phân trang ở Frontend)
    total = await db_manager.database["posts"].count_documents(query)

    # Format dữ liệu trả về
    formatted_posts = []
    for p in posts:
        p["id"] = str(p["_id"])
        del p["_id"]
        formatted_posts.append(p)

    return {"data": formatted_posts, "total": total, "page": page, "total_pages": (total // limit) + 1}

# --- API 2: CẬP NHẬT BÀI VIẾT (SỬA SENTIMENT / SPAM) ---
class PostUpdate(BaseModel):
    sentiment: Optional[str] = None
    is_spam: Optional[bool] = None

@app.put("/api/posts/{post_id}")
async def update_post(
    post_id: str, 
    update_data: PostUpdate,
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")

    if not ObjectId.is_valid(post_id):
        raise HTTPException(status_code=400, detail="Invalid ID")

    # Tạo dict update, loại bỏ các trường None
    fields = {k: v for k, v in update_data.dict().items() if v is not None}
    
    # Nếu sửa sentiment, tự động set độ tin cậy là 100%
    if "sentiment" in fields:
        fields["confidence_score"] = 1.0
        # Có thể thêm logic tính lại marketing_score ở đây nếu cần

    result = await db_manager.database["posts"].update_one(
        {"_id": ObjectId(post_id)},
        {"$set": fields}
    )
    
    return {"message": "Cập nhật thành công"}
# --- 9. API DASHBOARD (DÀNH CHO USER - KHÔI PHỤC LẠI) ---
@app.get("/api/dashboard/data")
async def get_dashboard_data(current_user: dict = Depends(get_current_user)):
    """
    Trả về dữ liệu bài viết (News + Youtube) để hiển thị lên Dashboard.
    Có lọc theo từ khóa/thương hiệu của User.
    """
    
    # 1. Tạo bộ lọc dựa trên cấu hình User
    filter_query = {}
    
    # Nếu là User thường (không phải Admin), chỉ xem bài liên quan đến Brand/Keywords của họ
    if current_user.get("role") != "admin":
        keywords = current_user.get("keywords", [])
        brand = current_user.get("brand_name", "")
        
        conditions = []
        # Lọc theo Brand Name (trong title hoặc content)
        if brand:
            conditions.append({"brand_name": brand})
            conditions.append({"title": {"$regex": brand, "$options": "i"}})
        
        # Lọc theo Keywords
        if keywords:
            clean_keywords = [k.strip() for k in keywords if k.strip()]
            if clean_keywords:
                keyword_regex = "|".join(clean_keywords)
                conditions.append({"title": {"$regex": keyword_regex, "$options": "i"}})
                conditions.append({"content": {"$regex": keyword_regex, "$options": "i"}})
        
        if conditions:
            filter_query = {"$or": conditions}
        else:
            # Nếu user không có keyword nào, trả về rỗng hoặc dữ liệu mẫu tùy logic
            return {"news": [], "youtube": []}

    # 2. Query Database (Lấy 50 bài mới nhất cho mỗi loại)
    try:
        # Lấy bài viết News
        news_cursor = db_manager.database["posts"].find({
            "platform": "news", 
            **filter_query
        }).sort("published_at", -1).limit(50)
        news_data = await news_cursor.to_list(length=50)
        
        # Lấy bài viết Youtube
        yt_cursor = db_manager.database["posts"].find({
            "platform": "youtube",
            **filter_query
        }).sort("published_at", -1).limit(50)
        yt_data = await yt_cursor.to_list(length=50)
    except Exception as e:
        print(f"Lỗi query dashboard: {e}")
        return {"news": [], "youtube": []}

    # 3. Helper chuyển ObjectId thành string (để tránh lỗi JSON)
    def format_data(items):
        formatted = []
        for item in items:
            item["id"] = str(item["_id"]) # Convert _id -> id
            del item["_id"]
            formatted.append(item)
        return formatted

    return {
        "news": format_data(news_data),
        "youtube": format_data(yt_data)
    }
@app.post("/api/analyze-url")
async def analyze_url(req: AnalyzeRequest, current_user: dict = Depends(get_current_user)):
    url = req.url.strip()
    
    # --- BƯỚC 1: LẤY TỪ KHÓA TỪ DB USER ---
    user_keywords = current_user.get("keywords", [])
    keywords_list = []
    
    if isinstance(user_keywords, list):
        keywords_list = [str(k).strip().lower() for k in user_keywords if k]
    elif isinstance(user_keywords, str):
        keywords_list = [k.strip().lower() for k in user_keywords.split(",") if k.strip()]

    # --- BƯỚC 2: VALIDATION URL ---
    is_youtube = "youtube.com" in url or "youtu.be" in url
    is_news = url.startswith("http") and not ("facebook.com" in url or "tiktok.com" in url)
    
    if not (is_youtube or is_news):
        raise HTTPException(status_code=400, detail="Hiện tại chỉ hỗ trợ link YouTube hoặc Báo chí.")

    # --- BƯỚC 3: THU THẬP DỮ LIỆU (CRAWLING) ---
    title = ""
    full_content = ""
    platform = "news"
    views = 0
    # [THAY ĐỔI] Khởi tạo các biến tương tác riêng biệt
    likes = 0
    comments = 0
    shares = 0
    published_at = datetime.now()

    try:
        if is_youtube:
            platform = "youtube"
            ydl_opts = {
                'quiet': True, 
                'skip_download': True, 
                'ignoreerrors': True, 
                'extract_flat': True 
            }
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info: raise Exception("Không tìm thấy thông tin video")
                
                title = info.get('title', '')
                video_id = info.get('id')
                
                # [CẬP NHẬT] Lấy chỉ số chi tiết
                views = info.get('view_count', 0) or 0
                likes = info.get('like_count', 0) or 0
                comments = info.get('comment_count', 0) or 0
                shares = info.get('repost_count', 0) or 0 # YoutubeDL đôi khi trả về cái này
                
                # Lấy Transcript
                transcript = get_youtube_transcript(video_id)
                full_content = transcript if transcript else info.get('description', '')

        else:
            # Logic cho Báo chí
            platform = "news"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            resp = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            title = soup.title.string.strip() if soup.title else url
            paragraphs = soup.find_all('p')
            full_content = " ".join([p.get_text() for p in paragraphs])
            
            # Giả lập chỉ số cho báo chí
            views = 1000 
            likes = 0
            comments = 0
            shares = 0

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lỗi khi đọc đường dẫn: {str(e)}")

    if len(full_content) < 50:
        raise HTTPException(status_code=400, detail="Nội dung quá ngắn hoặc không thể đọc được.")

    # --- BƯỚC 4: PHÂN TÍCH AI ---
    summary = gemini_summarize(full_content)
    sentiment_score = sentiment_model.predict(summary)
    
    sentiment_label = "NEUTRAL"
    if sentiment_score > 0.15: sentiment_label = "POSITIVE"
    elif sentiment_score < -0.15: sentiment_label = "NEGATIVE"
    
    # [CẬP NHẬT] Gọi hàm tính điểm mới với đầy đủ tham số
    marketing_score = calculate_marketing_score(
        sentiment_score=sentiment_score, 
        views=views, 
        likes=likes, 
        comments=comments, 
        shares=shares, 
        platform=platform # Truyền platform để kích hoạt logic bù điểm cho Youtube
    )

    # --- BƯỚC 5: KIỂM TRA TỪ KHÓA & LƯU DB ---
    has_keyword = False
    matched_keyword = ""
    content_check = (title + " " + full_content).lower()
    
    if keywords_list:
        for kw in keywords_list:
            if kw in content_check:
                has_keyword = True
                matched_keyword = kw
                break

    if has_keyword:
        post_doc = {
            "platform": platform,
            "source_url": url,
            "source_name": "Quick Analysis",
            "title": title,
            "content": summary,
            "original_content_snippet": full_content[:2000],
            "sentiment": sentiment_label,
            "sentiment_score": float(sentiment_score),
            "marketing_score": float(marketing_score),
            "views_count": views,
            "likes_count": likes,
            "comments_count": comments, # Lưu thêm comment count
            "shares_count": shares,     # Lưu thêm share count
            "published_at": published_at,
            "created_at": datetime.now(),
            "keywords_matched": [matched_keyword],
            "is_manual_analysis": True,
            "user_id": str(current_user["_id"])
        }
        await db_manager.database["posts"].insert_one(post_doc)
        
        # Ghi log
        if log_activity:
            log_msg = f"Phân tích: {url} | Điểm MKT: {marketing_score} | Khớp: {matched_keyword}"
            await log_activity("INFO", current_user["email"], "QUICK_ANALYSIS", log_msg)

    return {
        "title": title,
        "platform": platform,
        "content_snippet": summary,
        "sentiment": sentiment_label,
        "sentiment_score": round(float(sentiment_score), 3),
        "marketing_score": round(float(marketing_score), 1),
        "has_keyword": has_keyword,
        "matched_keyword": matched_keyword,
        "saved": has_keyword
    }

# 2. API Lấy thông tin User hiện tại (để hiển thị lên form)
@app.get("/api/users/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    # Chuyển đổi list keywords trong DB thành chuỗi để Frontend dễ hiển thị
    keywords_list = current_user.get("keywords", [])
    keywords_str = ""
    
    if isinstance(keywords_list, list):
        keywords_str = ", ".join(keywords_list)
    elif isinstance(keywords_list, str):
        keywords_str = keywords_list

    return {
        "email": current_user["email"],
        "username": current_user.get("username", ""),
        "role": current_user.get("role", "user"),
        "brand_name": current_user.get("brand_name", ""),
        "keywords": keywords_str,
        "active_sources": current_user.get("active_sources", {"youtube": True, "news": True})
    }

# 3. API Cập nhật Cài đặt
@app.put("/api/users/settings")
async def update_user_settings(settings_data: UserSettingsUpdate, current_user: dict = Depends(get_current_user)):
    # Xử lý chuỗi từ khóa thành List để lưu DB cho chuẩn
    raw_keywords = settings_data.keywords
    keywords_list = [k.strip() for k in raw_keywords.split(",") if k.strip()]
    
    update_data = {
        "brand_name": settings_data.brand_name,
        "keywords": keywords_list, # Lưu dạng List ["a", "b"]
        "active_sources": settings_data.active_sources,
        "updated_at": datetime.now()
    }
    
    # Cập nhật vào MongoDB
    await db_manager.database["users"].update_one(
        {"email": current_user["email"]},
        {"$set": update_data}
    )
    if log_activity:
        log_msg = f"Đổi Brand: {settings_data.brand_name} | Keywords: {len(keywords_list)} từ"
        await log_activity("INFO", current_user["email"], "UPDATE_SETTINGS", log_msg)
    return {"message": "Cập nhật thành công", "data": update_data}
@app.post("/api/users/change-password")
async def change_user_password(req: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    # Kiểm tra mật khẩu cũ
    if not verify_password(req.current_password, current_user["password"]):
        raise HTTPException(status_code=400, detail="Mật khẩu hiện tại không đúng")
    
    # Mã hóa mật khẩu mới
    hashed_new_password = get_password_hash(req.new_password)
    
    # Cập nhật vào DB
    await db_manager.database["users"].update_one(
        {"email": current_user["email"]},
        {"$set": {"password": hashed_new_password, "updated_at": datetime.now()}}
    )
    if log_activity:
        await log_activity("SUCCESS", current_user["email"], "CHANGE_PASSWORD", "Người dùng tự đổi mật khẩu")
    return {"message": "Đổi mật khẩu thành công"}
@app.post("/api/auth/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, background_tasks: BackgroundTasks):
    # 1. Kiểm tra email có tồn tại không
    user = await db_manager.get_user_by_email(req.email)
    if not user:
        # Trả về 404 nếu không tìm thấy email
        raise HTTPException(status_code=404, detail="Email không tồn tại trong hệ thống")

    # 2. Tạo mật khẩu mới ngẫu nhiên (8 ký tự)
    alphabet = string.ascii_letters + string.digits
    new_raw_password = ''.join(secrets.choice(alphabet) for i in range(8))
    
    # 3. Mã hóa mật khẩu mới
    hashed_password = get_password_hash(new_raw_password)

    # 4. Lưu vào Database
    await db_manager.database["users"].update_one(
        {"email": req.email},
        {"$set": {"password": hashed_password}}
    )

    # 5. Gửi Email (Chạy nền)
    if send_new_account_email: # Kiểm tra module email có load được không
        # Import hàm send_reset_password_email ở đầu file hoặc gọi từ module
        from backend.services.email_service import send_reset_password_email
        background_tasks.add_task(send_reset_password_email, req.email, new_raw_password)
    else:
        print("⚠️ Module Email chưa được cấu hình")

    return {"message": "Mật khẩu mới đã được gửi vào email của bạn."}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)