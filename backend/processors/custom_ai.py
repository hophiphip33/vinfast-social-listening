import os
import joblib
import re
from loguru import logger

# --- 1. MOCK DATA PROCESSOR (Để tránh lỗi thiếu file DataProcessor) ---
# Nếu bạn đã có file backend/processors/data_processor.py thì có thể xóa class này
# và uncomment dòng import bên dưới.
# from backend.processors.data_processor import DataProcessor

class DataProcessor:
    @staticmethod
    def clean_text(text: str) -> str:
        """Hàm làm sạch text đơn giản nếu chưa có module riêng"""
        if not text: return ""
        text = text.lower()
        text = re.sub(r'http\S+', '', text) # Xóa link
        text = re.sub(r'[^\w\s]', '', text) # Xóa ký tự đặc biệt
        return text.strip()

# --- 2. CLASS MODEL CỦA BẠN (Đã tối ưu) ---
class CustomSentimentModel:
    _instance = None

    def __new__(cls, *args, **kwargs):
        # Singleton Pattern: Đảm bảo chỉ load model 1 lần duy nhất
        if cls._instance is None:
            cls._instance = super(CustomSentimentModel, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_dir="backend/models"):
        if self._initialized:
            return
            
        self.model = None
        self.vectorizer = None
        self.model_dir = model_dir
        self._load_models()
        self._initialized = True

    def _load_models(self):
        """Load model và vectorizer từ file .pkl"""
        try:
            # Lấy đường dẫn tuyệt đối
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            # Điều chỉnh path trỏ về folder models
            model_folder = os.path.join(base_path, "models")
            
            model_path = os.path.join(model_folder, "model.pkl")
            vectorizer_path = os.path.join(model_folder, "vectorizer.pkl")

            if not os.path.exists(model_path) or not os.path.exists(vectorizer_path):
                logger.warning(f"⚠️ Không tìm thấy model tại: {model_path}")
                return

            logger.info(f"🔄 Đang load AI Model từ {model_path}...")
            self.model = joblib.load(model_path)
            self.vectorizer = joblib.load(vectorizer_path)
            logger.info("✅ Load AI Model thành công!")
            
        except Exception as e:
            logger.error(f"❌ Lỗi khi load model: {e}")

    def predict(self, text: str) -> float:
        """Trả về điểm số từ -1.0 đến 1.0"""
        if not self.model or not self.vectorizer:
            return 0.0
        
        if not text or len(text.strip()) == 0:
            return 0.0

        try:
            # Dùng class DataProcessor giả lập ở trên hoặc import thật
            clean_text = DataProcessor.clean_text(text)
            text_vector = self.vectorizer.transform([clean_text])
            
            # Tính toán xác suất
            if hasattr(self.model, "predict_proba"):
                probs = self.model.predict_proba(text_vector)[0]
                classes = self.model.classes_
                
                neg_idx = -1
                pos_idx = -1
                
                # Tìm index của nhãn NEG và POS
                for i, label in enumerate(classes):
                    lbl_str = str(label).upper()
                    if "NEG" in lbl_str or lbl_str == "-1": neg_idx = i
                    if "POS" in lbl_str or lbl_str == "1": pos_idx = i
                
                neg_prob = probs[neg_idx] if neg_idx != -1 else 0.0
                pos_prob = probs[pos_idx] if pos_idx != -1 else 0.0
                
                # Score = Positive - Negative
                score = pos_prob - neg_prob
                return float(score)
            else:
                # Fallback nếu model không hỗ trợ predict_proba
                pred = self.model.predict(text_vector)[0]
                return 1.0 if str(pred) == "POS" else -1.0

        except Exception as e:
            logger.error(f"Lỗi dự đoán: {e}")
            return 0.0

# --- 3. HÀM WRAPPER (Cầu nối cho Main.py) ---
# Đây là hàm mà main.py đang tìm kiếm
def analyze_sentiment(text: str):
    """
    Hàm này được gọi từ main.py.
    Nó khởi tạo class CustomSentimentModel và trả về định dạng chuẩn.
    """
    model_instance = CustomSentimentModel()
    score = model_instance.predict(text)
    
    # Quy đổi điểm số ra Nhãn (Label) để hiển thị
    if score > 0.1:
        label = "Positive"
    elif score < -0.1:
        label = "Negative"
    else:
        label = "Neutral"
        
    return {
        "label": label,
        "score": score
    }