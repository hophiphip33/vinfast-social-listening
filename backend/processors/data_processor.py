import re
import html
from typing import List, Dict
from backend.database.connection import DatabaseOperations
from loguru import logger
class DataProcessor:
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Làm sạch văn bản: chuyển chữ thường, xóa HTML, xóa ký tự đặc biệt, xóa link.
        """
        if not text:
            return ""
        
        # 1. Chuyển về chữ thường
        text = str(text).lower()
        
        # 2. Xóa HTML tags (nếu có)
        text = html.unescape(text)
        text = re.sub(r'<[^>]+>', '', text)
        
        # 3. Xóa URL
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # 4. Xóa Email
        text = re.sub(r'\S+@\S+', '', text)
        
        # 5. Xóa ký tự đặc biệt và số (giữ lại chữ cái tiếng Việt)
        # Regex này giữ lại các ký tự từ a-z, số 0-9 và các dấu tiếng Việt
        text = re.sub(r'[^\w\sàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', ' ', text)
        
        # 6. Xóa khoảng trắng thừa
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    @staticmethod
    def normalize_comment(comment_data: dict) -> dict:
        """
        Hàm hỗ trợ chuẩn hóa 1 object comment trước khi lưu DB
        """
        if "text" in comment_data:
            comment_data["text_clean"] = DataProcessor.clean_text(comment_data["text"])
        return comment_data

    @staticmethod
    def extract_keywords(text: str) -> List[str]:
        """
        Trích xuất từ khóa đơn giản (fallback nếu không dùng model chuyên sâu).
        Tách từ và lọc bỏ các từ dừng (stopwords) cơ bản.
        """
        if not text:
            return []
        
        clean_text = DataProcessor.clean_text(text)
        words = clean_text.split()
        
        # Danh sách từ dừng cơ bản tiếng Việt (ví dụ rút gọn)
        stopwords = {
            "là", "và", "của", "thì", "mà", "nhưng", "để", "với", "có", "được", 
            "cho", "về", "các", "những", "này", "cái", "con", "người", "khi",
            "trong", "đã", "đang", "sẽ", "rất", "cũng"
        }
        
        # Lọc từ: không nằm trong stopwords và độ dài > 1
        keywords = [w for w in words if w not in stopwords and len(w) > 1]
        
        # Trả về danh sách unique, giới hạn 10 từ
        return list(set(keywords))[:10]
    async def calculate_comprehensive_score(self, post_id: str):
        """
        Tính toán lại toàn bộ điểm số cho bài viết:
        1. Phân tích lại nội dung (nếu chưa có)
        2. Tính trung bình điểm bình luận (Crowd Score)
        3. Tính điểm tổng hợp (Weighted Score)
        """
        db_ops = DatabaseOperations()
        
        # 1. Lấy thông tin bài viết
        post = await db_ops.get_post_by_id(post_id)
        if not post:
            return None

        # 2. Lấy điểm Content (AI Sentiment Raw)
        # Nếu đã có rồi thì dùng, chưa có thì gọi model predict lại
        ai_score = post.get('ai_sentiment_raw')
        if ai_score is None:
            # Import lười để tránh lỗi vòng lặp
            from backend.processors.custom_ai import CustomSentimentModel
            model = CustomSentimentModel()
            
            # Kết hợp tiêu đề và nội dung để phân tích
            full_text = f"{post.get('title', '')} {post.get('content', '')}"
            ai_score = model.predict(full_text)

        # 3. Tính điểm Dư luận (Crowd Sentiment) từ Comments
        comments = await db_ops.get_comments_by_post_id(post_id)
        crowd_score = 0.0
        
        if comments:
            valid_scores = [
                c.get('sentiment_score', 0.0) 
                for c in comments 
                if c.get('sentiment_score') is not None
            ]
            if valid_scores:
                crowd_score = sum(valid_scores) / len(valid_scores)
        
        # 4. Tính điểm Tổng hợp (Marketing Score)
        # CÔNG THỨC: 60% Nội dung bài báo + 40% Phản ứng dư luận
        # Bạn có thể điều chỉnh tỷ lệ này (ví dụ: tin tiêu cực thì comment quan trọng hơn)
        weight_content = 0.6
        weight_crowd = 0.4
        
        # Nếu không có comment, điểm bài viết quyết định 100%
        if not comments:
            final_score = ai_score
        else:
            final_score = (ai_score * weight_content) + (crowd_score * weight_crowd)

        # Xác định nhãn (Label) cuối cùng
        final_label = "neutral"
        if final_score > 0.15: final_label = "positive"
        elif final_score < -0.15: final_label = "negative"

        # 5. Cập nhật vào Database
        update_data = {
            "ai_sentiment_raw": ai_score,     # Điểm máy chấm bài viết
            "crowd_sentiment": crowd_score,   # Điểm trung bình comment
            "sentiment_score": final_score,   # Điểm số cuối cùng
            "sentiment": final_label,         # Nhãn cuối cùng
            "is_processed": True
        }
        
        await db_ops.update_post_analysis(post_id, update_data)
        logger.info(f"Updated score for {post_id}: AI={ai_score:.2f}, Crowd={crowd_score:.2f} -> Final={final_score:.2f}")
        
        return update_data
    

# --- QUAN TRỌNG: Khởi tạo instance để các module khác import ---
data_processor = DataProcessor()