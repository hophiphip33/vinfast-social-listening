from backend.database.connection import db_manager
from datetime import datetime

async def log_activity(level: str, actor: str, action: str, details: str):
    """
    Hàm helper để ghi log vào MongoDB.
    - level: INFO, ERROR, WARNING, SUCCESS
    - actor: "SYSTEM" hoặc email user
    - action: Mã hành động ngắn gọn
    - details: Nội dung chi tiết
    """
    try:
        # Đảm bảo DB đã kết nối
        if db_manager.database is None:
            await db_manager.connect()
            
        log_entry = {
            "level": level,
            "actor": actor,
            "action": action,
            "details": details,
            "created_at": datetime.now()
        }
        
        await db_manager.database["system_logs"].insert_one(log_entry)
        print(f"📝 LOG [{level}] {action}: {details}")
        
    except Exception as e:
        print(f"❌ Không thể ghi log: {e}")