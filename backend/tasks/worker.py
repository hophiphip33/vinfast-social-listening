# Ví dụ về Celery task mới trong backend/tasks/worker.py

from backend.collectors.youtube_collector import get_video_info
from backend.collectors.news_collector import NewsCollector
from backend.database.connection import DatabaseOperations

@app.task
def collect_single_url_task(url: str):
    """Collects, processes, and analyzes a single URL"""
    db_ops = DatabaseOperations()
    analyzer = sentiment_analyzer # Lấy instance analyzer

    if "youtube.com" in url or "youtu.be" in url:
        # Xử lý YouTube
        video_post_data, comments_list = get_video_info(url)
        if video_post_data:
            post_id = asyncio.run(db_ops.insert_post(video_post_data))
            if post_id and comments_list:
                # Lưu và phân tích comment
                # Chú ý: Cần viết lại logic này để sử dụng db_ops và analyzer một cách async
                # Ví dụ: async def save_comments_async(db_ops, post_id, comments, analyzer)
                pass # Logic lưu comment và phân tích...
            # Sau khi lưu, đảm bảo Post được Process (Sentiment)
            asyncio.run(data_processor.process_single_url(post_id)) # Giả định có hàm process_single_url
            return post_id

    elif any(source in url for source in ["vnexpress.net", "tuoitre.vn", "thanhnien.vn", "vietnamnet.vn"]):
        # Xử lý News
        async def collect_news_url():
            async with NewsCollector() as collector:
                # Giả định có hàm collect_single_article(url) trong NewsCollector
                article_data = await collector.collect_single_article(url)
                if article_data:
                    post_id = await db_ops.insert_post(article_data)
                    await data_processor.process_single_url(post_id)
                    return post_id
        return asyncio.run(collect_news_url())

    else:
        logger.warning(f"Unsupported URL platform: {url}")
        return None