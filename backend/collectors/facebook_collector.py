# backend/collectors/facebook_scraper.py
"""
Facebook Scraper - MIỄN PHÍ
Sử dụng: facebook-scraper library (unofficial but works)
Lấy: Posts, Comments, Reactions từ PUBLIC pages
"""

try:
    from facebook_scraper import get_posts, get_profile
except ImportError:
    print("⚠️  Please install: pip install facebook-scraper")

from datetime import datetime, timedelta
from typing import List, Dict
import time
import random

class FacebookScraper:
    """
    Scraper miễn phí cho Facebook PUBLIC pages
    - Không cần API key
    - Không cần đăng nhập (cho public pages)
    - Lấy được: posts, likes, shares, comments
    """
    
    def __init__(self, cookies_file=None):
        """
        cookies_file: Optional - file cookies.txt để tránh rate limit
        Để lấy cookies:
        1. Đăng nhập Facebook trên Chrome
        2. Cài extension "Get cookies.txt LOCALLY"
        3. Export cookies và lưu vào file
        """
        self.cookies_file = cookies_file
        self.delay_range = (2, 5)  # Delay giữa các requests để tránh block
    
    def search_public_pages(self, keywords: List[str]) -> List[Dict]:
        """
        Tìm các Facebook pages công khai liên quan đến keywords
        Note: Cần manual vì Facebook không cho search tự động
        """
        # Danh sách pages VinFast phổ biến (có thể mở rộng)
        vinfast_pages = [
            "VinFastAuto.Official",           # VinFast official
            "VinFastVietNam",        # VinFast Vietnam
            "VinFast.Owners",        # VinFast Owners Group (nếu public)
            "Otofun.Community",                # Oto.com.vn
            "xehay.vn",              # Xe Hay
            "autodaily.vn",          # Auto Daily
            "carpassion.vn"          # Car Passion
        ]
        
        return [{"page_id": page, "name": page} for page in vinfast_pages]
    
    def get_page_posts(
        self, 
        page_id: str, 
        keywords: List[str] = None,
        days_back: int = 14, 
        max_posts: int = 50
    ) -> List[Dict]:
        """
        Lấy posts từ một Facebook page công khai
        """
        posts_data = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        try:
            print(f"  → Scraping page: {page_id}")
            
            # Lấy posts từ page
            posts = get_posts(
                account=page_id,
                pages=max_posts,
                cookies=self.cookies_file,
                options={
                    "comments": True,      # Lấy comments
                    "reactors": True,      # Lấy reactions
                    "progress": False
                }
            )
            
            for post in posts:
                # Kiểm tra ngày đăng
                post_time = post.get("time")
                if post_time and post_time < cutoff_date:
                    break
                
                # Lấy text content
                text = post.get("text", "") or post.get("post_text", "")
                
                # Filter theo keywords nếu có
                if keywords:
                    text_lower = text.lower()
                    if not any(kw.lower() in text_lower for kw in keywords):
                        continue
                
                # Lấy comments
                comments_list = []
                comments_full = post.get("comments_full", []) or []
                for comment in comments_full[:100]:  # Giới hạn 100 comments đầu
                    comments_list.append({
                        "comment_id": comment.get("comment_id"),
                        "author": comment.get("commenter_name"),
                        "text": comment.get("comment_text", ""),
                        "likes": comment.get("comment_reaction_count", 0),
                        "time": comment.get("comment_time")
                    })
                
                # Lấy reactions (likes, love, haha, etc.)
                reactions = post.get("reactions", {}) or {}
                
                post_data = {
                    "post_id": post.get("post_id"),
                    "url": post.get("post_url", ""),
                    "author": page_id,
                    "content": text,
                    "published": post_time,
                    "likes": reactions.get("like", 0),
                    "love": reactions.get("love", 0),
                    "haha": reactions.get("haha", 0),
                    "wow": reactions.get("wow", 0),
                    "sad": reactions.get("sad", 0),
                    "angry": reactions.get("angry", 0),
                    "total_reactions": sum(reactions.values()) if reactions else 0,
                    "shares": post.get("shares", 0),
                    "comments_count": post.get("comments", 0),
                    "comments": comments_list,
                    "image": post.get("image", ""),
                    "video": post.get("video", "")
                }
                
                posts_data.append(post_data)
                
                # Delay để tránh bị block
                time.sleep(random.uniform(*self.delay_range))
                
        except Exception as e:
            print(f"  ⚠️  Error scraping {page_id}: {e}")
        
        return posts_data
    
    def search_posts_by_keywords(
        self, 
        keywords: List[str], 
        days_back: int = 14,
        max_posts_per_page: int = 30
    ) -> List[Dict]:
        """
        Main method: Lấy tất cả posts từ các pages liên quan
        """
        all_posts = []
        pages = self.search_public_pages(keywords)
        
        print(f"\n🔍 Searching {len(pages)} Facebook pages...")
        
        for page in pages:
            try:
                posts = self.get_page_posts(
                    page["page_id"], 
                    keywords=keywords,
                    days_back=days_back, 
                    max_posts=max_posts_per_page
                )
                all_posts.extend(posts)
                print(f"  ✓ Found {len(posts)} posts from {page['page_id']}")
                
                # Delay giữa các pages
                time.sleep(random.uniform(3, 6))
                
            except Exception as e:
                print(f"  ✗ Failed to scrape {page['page_id']}: {e}")
                continue
        
        return all_posts


class FacebookGroupScraper:
    """
    Scraper cho Facebook PUBLIC Groups
    """
    
    def __init__(self, cookies_file=None):
        self.cookies_file = cookies_file
    
    def get_group_posts(
        self, 
        group_id: str, 
        keywords: List[str] = None,
        days_back: int = 14,
        max_posts: int = 50
    ) -> List[Dict]:
        """
        Lấy posts từ PUBLIC Facebook group
        group_id: ID hoặc username của group
        """
        posts_data = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        try:
            print(f"  → Scraping group: {group_id}")
            
            posts = get_posts(
                group=group_id,  # Sử dụng 'group' thay vì 'account'
                pages=max_posts,
                cookies=self.cookies_file,
                options={
                    "comments": True,
                    "reactors": True,
                    "progress": False
                }
            )
            
            for post in posts:
                post_time = post.get("time")
                if post_time and post_time < cutoff_date:
                    break
                
                text = post.get("text", "") or post.get("post_text", "")
                
                # Filter theo keywords
                if keywords:
                    text_lower = text.lower()
                    if not any(kw.lower() in text_lower for kw in keywords):
                        continue
                
                # Lấy comments
                comments_list = []
                for comment in (post.get("comments_full") or [])[:100]:
                    comments_list.append({
                        "comment_id": comment.get("comment_id"),
                        "author": comment.get("commenter_name"),
                        "text": comment.get("comment_text", ""),
                        "likes": comment.get("comment_reaction_count", 0)
                    })
                
                reactions = post.get("reactions", {}) or {}
                
                post_data = {
                    "post_id": post.get("post_id"),
                    "url": post.get("post_url", ""),
                    "author": post.get("username", "Unknown"),
                    "content": text,
                    "published": post_time,
                    "total_reactions": sum(reactions.values()) if reactions else 0,
                    "shares": post.get("shares", 0),
                    "comments_count": post.get("comments", 0),
                    "comments": comments_list
                }
                
                posts_data.append(post_data)
                time.sleep(random.uniform(2, 4))
                
        except Exception as e:
            print(f"  ⚠️  Error scraping group {group_id}: {e}")
        
        return posts_data

if __name__ == "__main__":
    print("🚀 Đang chạy thử FacebookScraper...\n")

    scraper = FacebookScraper()
    keywords = ["VinFast", "VF8", "xe điện"]
    
    posts = scraper.search_posts_by_keywords(
        keywords=keywords,
        days_back=2,
        max_posts_per_page=1
    )

    print(f"\n✅ Tổng số bài viết lấy được: {len(posts)}")
    if posts:
        print("📄 Bài viết mẫu:")
        print(posts[0])
    else:
        print("⚠️ Không tìm thấy bài viết nào.")

# HƯỚNG DẪN SỬ DỤNG:
"""
# 1. Cài đặt thư viện
pip install facebook-scraper

# 2. Không cần cookies (cho public pages)
from collectors.facebook_scraper import FacebookScraper

scraper = FacebookScraper()
keywords = ["VinFast", "VF8", "xe điện"]
posts = scraper.search_posts_by_keywords(keywords, days_back=14)

# 3. Có cookies (tốt hơn, tránh rate limit)
scraper = FacebookScraper(cookies_file="facebook_cookies.txt")
posts = scraper.search_posts_by_keywords(keywords, days_back=14)

# 4. Scrape group công khai
from collectors.facebook_scraper import FacebookGroupScraper

group_scraper = FacebookGroupScraper(cookies_file="facebook_cookies.txt")
posts = group_scraper.get_group_posts(
    group_id="VinFastOwnersVietnam",  # Ví dụ
    keywords=["VF8", "lỗi"],
    days_back=7
)

# 5. Kết quả bao gồm:
# - Post content, reactions (like, love, haha, sad, angry)
# - Comments với author và likes
# - Shares count
# - URL, images, videos
"""