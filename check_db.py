import asyncio
import os
import sys

# Setup đường dẫn
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database.connection import db_manager
from backend.config.settings import settings

async def debug_db():
    print("----------- KIỂM TRA DATABASE -----------")
    print(f"🔌 URL:      {settings.mongodb_url}")
    print(f"🗄️  DB Name:  {settings.database_name}")
    
    try:
        await db_manager.connect()
        # Lấy danh sách user
        users = await db_manager.database['users'].find().to_list(100)
        
        print(f"👥 Tổng số user tìm thấy: {len(users)}")
        
        if len(users) == 0:
            print("❌ DATABASE ĐANG TRỐNG! Bạn chưa chạy script tạo admin thành công.")
        else:
            print("✅ Danh sách tài khoản hiện có:")
            for u in users:
                print(f"   👉 Email: '{u.get('email')}' | Pass (Hash): {u.get('password')[:10]}... | Role: {u.get('role')}")
                
    except Exception as e:
        print(f"❌ Lỗi kết nối: {e}")
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(debug_db())