# test_email.py
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

# Load file .env
load_dotenv()

SMTP_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("MAIL_PORT", 587))
SENDER_EMAIL = os.getenv("MAIL_USERNAME")
SENDER_PASSWORD = os.getenv("MAIL_PASSWORD")

def test_send():
    print(f"Đang thử kết nối tới {SMTP_SERVER}:{SMTP_PORT}...")
    print(f"Tài khoản: {SENDER_EMAIL}")
    
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("❌ Lỗi: Chưa đọc được biến môi trường. Kiểm tra file .env")
        return

    try:
        msg = MIMEText("Đây là email kiểm tra từ VinFast Social Listening.")
        msg['Subject'] = "Test Email Connection"
        msg['From'] = SENDER_EMAIL
        msg['To'] = SENDER_EMAIL  # Gửi cho chính mình để test

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.set_debuglevel(1)  # Hiện chi tiết quá trình kết nối
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("\n✅ GỬI THÀNH CÔNG! Cấu hình của bạn đã đúng.")
    except Exception as e:
        print(f"\n❌ GỬI THẤT BẠI: {e}")

if __name__ == "__main__":
    test_send()