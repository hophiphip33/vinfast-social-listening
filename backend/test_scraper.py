"""
Facebook Scraper Test Script
Tác giả: ChatGPT
Hướng dẫn:
1️⃣ Lưu file này vào thư mục backend/
2️⃣ Đảm bảo file cookies.json nằm trong backend/collectors/
3️⃣ Chạy: python -m backend.test_scraper
"""

import os
import json
import time
from facebook_scraper import get_posts, set_cookies
from datetime import datetime

# 🧩 Đường dẫn cookie
COOKIE_PATH = os.path.join(os.path.dirname(__file__), "collectors", "cookies.json")

# 🔍 Danh sách các page cần quét (chính xác tên Facebook handle)
PAGES = [
    "VinFastAuto",
    "VinFastVietNam",
    "VinFast.Owners",
    "otofun",
    "xehay.vn",
    "carpassion.vn",
    "autopro.vn"
]

# 📦 File lưu kết quả
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "vinfast_posts.json")


def test_scraper():
    print("🔍 Bắt đầu thu thập bài viết...\n")

    # Kiểm tra cookie
    if not os.path.exists(COOKIE_PATH):
        print(f"❌ Không tìm thấy file cookie tại {COOKIE_PATH}")
        return

    # Nạp cookie
    try:
        set_cookies(COOKIE_PATH)
        print("✅ Cookie đã được tải thành công!\n")
    except Exception as e:
        print(f"❌ Lỗi khi tải cookie: {e}")
        return

    all_posts = []

    print(f"🔍 Searching {len(PAGES)} Facebook pages...")
    for page in PAGES:
        print(f"  → Scraping page: {page}")
        try:
            posts = []
            # Lấy tối đa 5 bài gần nhất để test
            for post in get_posts(page, pages=1, timeout=30):
                posts.append({
                    "page": page,
                    "time": post.get("time"),
                    "text": post.get("text")[:300] if post.get("text") else "",
                    "likes": post.get("likes"),
                    "comments": post.get("comments"),
                    "shares": post.get("shares"),
                    "post_url": post.get("post_url"),
                })
            print(f"  ✓ Found {len(posts)} posts from {page}")
            all_posts.extend(posts)
        except Exception as e:
            print(f"  ⚠️  Error scraping {page}: {e}")
        # ⏳ Tránh bị chặn
        time.sleep(5)

    # Lưu kết quả
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_posts, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Tổng số bài viết thu được: {len(all_posts)}")
    print(f"💾 Đã lưu kết quả vào {OUTPUT_FILE}")


if __name__ == "__main__":
    test_scraper()
