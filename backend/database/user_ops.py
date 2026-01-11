"""
backend/database/user_ops.py
Module chuyên biệt để quản lý User (Khách hàng) trong MongoDB
"""
from .connection import db_manager
from bson.objectid import ObjectId
from datetime import datetime
from typing import List

class UserOperations:
    
    @staticmethod
    async def get_all_users():
        """Lấy danh sách toàn bộ khách hàng"""
        # Sửa .db thành .database
        if db_manager.database is None: await db_manager.connect()
        
        users_cursor = db_manager.database['users'].find().sort("created_at", -1)
        users = await users_cursor.to_list(length=1000)
        # Chuyển ObjectId thành string để hiển thị
        for u in users:
            u['_id'] = str(u['_id'])
        return users

    @staticmethod
    async def create_user(username, email, password, plan="Free", role="user", keywords=[]):
        """
        Tạo user mới với phân quyền
        role: 'user' (mặc định) hoặc 'admin'
        """
        # Sửa .db thành .database
        if db_manager.database is None: await db_manager.connect()
        
        # Kiểm tra xem email đã tồn tại chưa
        existing_user = await db_manager.database['users'].find_one({"email": email})
        if existing_user:
            return None # Hoặc báo lỗi

        new_user = {
            "username": username,
            "email": email,
            "password": password, # Lưu ý: Thực tế nên hash password trước khi lưu
            "role": role,         # <--- Lưu quyền vào đây
            "plan": plan,
            "keywords": keywords, # Lưu danh sách từ khóa
            "is_active": True,
            "created_at": datetime.now()
        }
        result = await db_manager.database['users'].insert_one(new_user)
        return str(result.inserted_id)

    @staticmethod
    async def update_user(user_id, update_data):
        """Cập nhật thông tin khách hàng (Gói, Trạng thái)"""
        if db_manager.database is None: await db_manager.connect()
        try:
            await db_manager.database['users'].update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            return True
        except:
            return False

    @staticmethod
    async def delete_user(user_id):
        """Xóa khách hàng"""
        if db_manager.database is None: await db_manager.connect()
        try:
            await db_manager.database['users'].delete_one({"_id": ObjectId(user_id)})
            return True
        except:
            return False

    @staticmethod
    async def get_all_active_keywords():
        """
        Lấy TẤT CẢ từ khóa của những user đang hoạt động (Active).
        Dùng để Crawler biết cần quét những từ nào.
        """
        if db_manager.database is None: await db_manager.connect()
        
        # Chỉ lấy user đang active
        cursor = db_manager.database['users'].find({"is_active": True}, {"keywords": 1})
        users = await cursor.to_list(length=1000)
        
        # Gộp tất cả từ khóa lại và loại bỏ trùng lặp (Set)
        all_keywords = set()
        for u in users:
            if "keywords" in u and isinstance(u["keywords"], list):
                all_keywords.update([k.lower().strip() for k in u["keywords"]])
        
        return list(all_keywords)

    @staticmethod
    async def update_user_keywords(user_id, keywords: List[str]):
        """Cập nhật danh sách từ khóa cho 1 user"""
        if db_manager.database is None: await db_manager.connect()
        await db_manager.database['users'].update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"keywords": keywords}}
        )