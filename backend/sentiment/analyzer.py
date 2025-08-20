# backend/sentiment/analyzer.py

class SentimentAnalyzer:
    def __init__(self):
        # Tập từ khóa mở rộng
        self.positive_words = [
            "tốt", "rất tốt", "quá tốt", "tuyệt vời",
            "đẹp", "ok", "ngon", "hài lòng", "yêu", "thích", "xuất sắc"
        ]
        self.negative_words = [
            "tệ", "rất tệ", "quá tệ", "xấu", "lỗi",
            "ghét", "dở", "kém", "thất vọng", "kinh khủng"
        ]

    def analyze_one(self, text: str):
        text = text.lower().strip()

        # Ưu tiên kiểm tra cụm từ
        for phrase in self.positive_words:
            if phrase in text:
                return {"label": "positive", "score": 0.9}
        for phrase in self.negative_words:
            if phrase in text:
                return {"label": "negative", "score": 0.9}

        # Nếu không có cụm → kiểm tra từng từ đơn
        words = text.split()
        if any(w in words for w in self.positive_words):
            return {"label": "positive", "score": 0.8}
        if any(w in words for w in self.negative_words):
            return {"label": "negative", "score": 0.8}

        return {"label": "neutral", "score": 0.5}
