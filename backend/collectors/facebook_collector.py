"""
Facebook Public Data Collector for VinFast Social Listening Platform
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import aiohttp
from facebook_scraper import get_posts
from loguru import logger

from backend.database.connection import DatabaseOperations
from backend.config.settings import settings


class FacebookCollector:
    """Collects public Facebook posts and comments about VinFast"""

    def __init__(self):
        self.db_ops = DatabaseOperations()
        self.session: Optional[aiohttp.ClientSession] = None

        # Các từ khóa liên quan VinFast
        self.vinfast_keywords = [
            "vinfast", "vin fast", "xe vinfast", "ô tô vinfast",
            "xe điện vinfast", "vingroup", "phạm nhật vượng",
            "vf8", "vf9", "vf5", "fadil", "lux a2.0", "lux sa2.0",
            "oto vinfast", "vinfast vietnam"
        ]

        # Các page công khai cần theo dõi
        self.target_pages = [
            "VinFastAuto.Official",
            "VinFastGlobal",
            "VinGroupOfficial",
            "otosaigon",
            "xehay.vn",
            "autodaily.vn",
        ]

    async def __aenter__(self):
        """Khởi tạo session HTTP (cho các request phụ nếu cần)"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            headers={"User-Agent": "Mozilla/5.0"}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Đóng session HTTP"""
        if self.session:
            await self.session.close()

    def _is_vinfast_related(self, text: str) -> bool:
        """Check nếu nội dung có chứa từ khóa VinFast"""
        if not text:
            return False
        return any(keyword in text.lower() for keyword in self.vinfast_keywords)

    def _extract_engagement_metrics(self, post_data: Dict[str, Any]) -> Dict[str, int]:
        """Lấy số like, share, comment từ post"""
        return {
            "likes_count": post_data.get("likes") or 0,
            "shares_count": post_data.get("shares") or 0,
            "comments_count": post_data.get("comments") or 0,
            "views_count": 0  # Không có trong free API
        }

    async def collect_from_page(self, page_name: str, max_posts: int = 20) -> List[Dict[str, Any]]:
        """Lấy dữ liệu post từ 1 fanpage"""
        collected_posts = []

        try:
            logger.info(f"Collecting posts from Facebook page: {page_name}")

            posts = get_posts(
                account=page_name,
                pages=max_posts // 10,  # facebook-scraper: mỗi page ~10 post
                extra_info=True,
                
                cookies="backend/config/facebook_cookies.txt"
            )

            for post in posts:
                post_text = (post.get("text") or "") + " " + (post.get("post_text") or "")

                # Bỏ qua nếu không liên quan VinFast
                #  continue

                engagement = self._extract_engagement_metrics(post)

                post_data = {
                    "platform": "facebook",
                    "source_url": post.get("post_url"),
                    "source_name": page_name,
                    "title": None,
                    "content": post_text.strip(),
                    "author": page_name,
                    "published_at": post.get("time") or datetime.now(),
                    "collected_at": datetime.now(),
                    **engagement,
                    "language": "vi",
                    "is_processed": False,
                }

                try:
                    # Lưu post vào DB và lấy id
                    post_id = await self.db_ops.insert_post(post_data)
                    post_data["_id"] = post_id
                    collected_posts.append(post_data)

                    # Nếu có comment thì lưu
                    if post.get("comments_full"):
                        await self._collect_comments(post, post_id)

                except Exception as e:
                    logger.warning(f"Error saving post from {page_name}: {e}")

                await asyncio.sleep(settings.social_crawl_delay)

            logger.info(f"Collected {len(collected_posts)} VinFast-related posts from {page_name}")
            return collected_posts

        except Exception as e:
            logger.error(f"Error collecting from Facebook page {page_name}: {e}")
            return []

    async def _collect_comments(self, post: Dict[str, Any], post_id: str):
        """Lưu comment của 1 post"""
        try:
            for comment in post.get("comments_full", []):
                comment_text = comment.get("comment_text", "")
                if not comment_text.strip():
                    continue

                comment_data = {
                    "post_id": post_id,
                    "content": comment_text,
                    "author": comment.get("commenter_name"),
                    "likes_count": comment.get("comment_reaction_count") or 0,
                    "replies_count": len(comment.get("replies", [])),
                    "published_at": comment.get("comment_time") or datetime.now(),
                    "collected_at": datetime.now(),
                    "language": "vi",
                    "is_processed": False
                }

                try:
                    await self.db_ops.insert_comment(comment_data)
                except Exception as e:
                    logger.warning(f"Error saving comment: {e}")

        except Exception as e:
            logger.error(f"Error collecting comments: {e}")

    async def collect_all_facebook_data(self) -> Dict[str, Any]:
        """Collect từ tất cả fanpage trong danh sách"""
        all_posts = []
        stats = {"pages": {}, "total_posts": 0}

        logger.info("Starting Facebook data collection...")

        for page_name in self.target_pages:
            posts = await self.collect_from_page(page_name, settings.max_posts_per_batch)
            all_posts.extend(posts)
            stats["pages"][page_name] = len(posts)

        stats["total_posts"] = len(all_posts)
        logger.info(f"Facebook collection completed. Total posts: {stats['total_posts']}")
        return stats


# Usage example
async def main():
    from backend.database.connection import db_manager
    await db_manager.connect()

    async with FacebookCollector() as collector:
        stats = await collector.collect_all_facebook_data()
        print(stats)

    await db_manager.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
