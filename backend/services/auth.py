from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from backend.config.settings import settings
from backend.database.connection import db_manager

# Cấu hình Hash mật khẩu
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Cấu hình OAuth2 (Token Url phải trùng với API login trong main.py)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- MODELS ---
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str = "user"

class TokenData(BaseModel):
    email: Optional[str] = None

# --- HÀM HỖ TRỢ BẢO MẬT ---

def verify_password(plain_password, hashed_password):
    """Kiểm tra mật khẩu nhập vào có khớp với hash trong DB không"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Mã hóa mật khẩu để lưu vào DB"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Tạo JWT Token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Dependency dùng để bảo vệ API. 
    Nó sẽ kiểm tra Token, nếu đúng -> trả về thông tin user.
    Nếu sai -> Báo lỗi 401.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Giải mã Token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
        
    # Tìm user trong Database
    user = await db_manager.get_user_by_email(email=token_data.email)
    if user is None:
        raise credentials_exception
        
    return user