from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from backend.config.settings import settings
from backend.services.logger_service import log_activity
from pydantic import EmailStr
from typing import List

# --- 1. CẤU HÌNH KẾT NỐI EMAIL (SỬA LỖI "conf is not defined") ---
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

# --- 2. CÁC HÀM GỬI EMAIL ---

async def send_new_account_email(to_email: str, username: str, password: str):
    """
    Gửi email thông báo tài khoản mới và ghi log hệ thống.
    """
    try:
        subject = "Chào mừng bạn đến với Veda Social Listening"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #2563eb;">Thông Tin Tài Khoản Mới</h2>
                <p>Xin chào <strong>{username}</strong>,</p>
                <p>Tài khoản của bạn đã được khởi tạo thành công trên hệ thống Social Listening.</p>
                <div style="background: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 5px 0;">Email đăng nhập: <b>{to_email}</b></p>
                    <p style="margin: 5px 0;">Mật khẩu: <b>{password}</b></p>
                </div>
                <p>Vui lòng đăng nhập và đổi mật khẩu ngay lập tức để bảo mật.</p>
                <hr style="border: 0; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #666;">VinFast Social Listening System</p>
            </body>
        </html>
        """

        message = MessageSchema(
            subject=subject,
            recipients=[to_email],
            body=html_content,
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message)

        # Ghi log thành công
        await log_activity(
            level="INFO", 
            actor="SYSTEM", 
            action="SEND_EMAIL", 
            details=f"Đã gửi email chào mừng tới {to_email}"
        )
        return True

    except Exception as e:
        print(f"❌ Lỗi gửi email (New Account): {e}")
        # Ghi log lỗi
        await log_activity(
            level="ERROR", 
            actor="SYSTEM", 
            action="EMAIL_FAIL", 
            details=f"Lỗi gửi mail tới {to_email}: {str(e)}"
        )
        return False


async def send_crisis_alert_email(to_email: str, brand_name: str, negative_posts: list):
    """
    Gửi email cảnh báo khủng hoảng (Crisis Alert).
    """
    try:
        subject = f"[Veda Social Listening] CẢNH BÁO KHỦNG HOẢNG: Phát hiện nội dung tiêu cực cho {brand_name}"
        
        # Tạo danh sách HTML các bài viết
        posts_html = ""
        for post in negative_posts:
            score = post.get('marketing_score', 0)
            url = post.get('source_url', '#')
            title = post.get('title', 'Không tiêu đề')
            platform = post.get('platform', 'Unknown').upper()
            
            posts_html += f"""
            <div style="margin-bottom: 15px; border-left: 4px solid #dc2626; padding-left: 10px; background-color: white; padding: 10px;">
                <p style="margin: 0; font-weight: bold; color: #333;">[{platform}] {title}</p>
                <p style="margin: 5px 0; font-size: 14px;">Điểm ảnh hưởng: <span style="color: #dc2626; font-weight: bold;">{score}/10</span></p>
                <a href="{url}" style="color: #2563eb; text-decoration: none; font-size: 14px;">👉 Xem chi tiết</a>
            </div>
            """

        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
            <h2 style="color: #dc2626; border-bottom: 2px solid #dc2626; padding-bottom: 10px;">⚠️ Cảnh Báo Nội dung Tiêu cực</h2>
            <p>Hệ thống vừa phát hiện <strong>{len(negative_posts)}</strong> nội dung có sắc thái tiêu cực và điểm ảnh hưởng cao đối với thương hiệu <strong>{brand_name}</strong>.</p>
            
            <div style="background-color: #fef2f2; padding: 15px; border-radius: 5px; margin: 20px 0; border: 1px solid #fecaca;">
                {posts_html}
            </div>
            
            <p>Vui lòng đăng nhập vào hệ thống để xử lý ngay lập tức.</p>
            <p style="font-size: 12px; color: #666; margin-top: 30px;">Email tự động từ hệ thống Social Listening.</p>
        </div>
        """

        message = MessageSchema(
            subject=subject,
            recipients=[to_email],
            body=html_content,
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message)
        return True

    except Exception as e:
        print(f"❌ Lỗi gửi email cảnh báo: {str(e)}")
        return False


async def send_reset_password_email(to_email: str, new_password: str):
    """
    Gửi email cấp lại mật khẩu mới.
    """
    try:
        html_content = f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #2563eb;">Yêu cầu cấp lại mật khẩu</h2>
            <p>Chào bạn,</p>
            <p>Hệ thống đã nhận được yêu cầu lấy lại mật khẩu cho tài khoản: <b>{to_email}</b></p>
            <p>Đây là mật khẩu mới của bạn:</p>
            <div style="background: #f4f4f5; padding: 15px; font-size: 24px; font-weight: bold; letter-spacing: 3px; text-align: center; margin: 20px 0; border-radius: 8px; border: 1px dashed #ccc;">
                {new_password}
            </div>
            <p>Vui lòng đăng nhập và <strong>đổi lại mật khẩu</strong> ngay lập tức để bảo mật tài khoản.</p>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="font-size: 12px; color: #666;">Nếu bạn không yêu cầu thay đổi này, vui lòng liên hệ quản trị viên ngay lập tức.</p>
        </div>
        """

        message = MessageSchema(
            subject="[Veda Social Listening] Cấp lại mật khẩu đăng nhập",
            recipients=[to_email],
            body=html_content,
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message)
        print(f"✅ Đã gửi email reset pass tới {to_email}")
        return True

    except Exception as e:
        print(f"❌ Lỗi gửi email reset password: {str(e)}")
        return False