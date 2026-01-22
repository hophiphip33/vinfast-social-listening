import asyncio
import os
import sys

# Thêm đường dẫn để Python tìm thấy module backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database.connection import db_manager
from backend.database.user_ops import UserOperations

async def init_data():
    print("⏳ Đang kết nối Database...")
    await db_manager.connect()
    
    print("👤 Đang tạo tài khoản Admin...")
    # Tạo Admin với quyền 'admin' và từ khóa mẫu
    result = await UserOperations.create_user(
        username="Admin",
        email="admin@vinfast.vn",
        password="admin123", # Password này chưa hash (để test)
        role="admin",        # Quan trọng: set quyền admin
    )
    
    if result:
        print(f"✅ Đã tạo thành công User ID: {result}")
        print("🚀 Bây giờ bạn hãy vào MongoDB Compass và Refresh lại, bảng 'users' sẽ xuất hiện!")
    else:
        print("⚠️ Email này đã tồn tại hoặc có lỗi xảy ra.")

    await db_manager.disconnect()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(init_data())