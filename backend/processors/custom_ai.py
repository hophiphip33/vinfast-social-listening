import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch.nn.functional as F
from loguru import logger
import os

class CustomSentimentModel:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(CustomSentimentModel, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.tokenizer = None
        self.model = None
        # Tên model trên HuggingFace hoặc đường dẫn folder local
        self.model_name = "wonrax/phobert-base-vietnamese-sentiment" 
        self._load_models()
        self._initialized = True

    def _load_models(self):
        try:
            logger.info(f"🔄 Đang load PhoBERT từ {self.model_name}...")
            # Load Tokenizer và Model từ HuggingFace
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            
            # Chuyển sang chế độ eval (không train)
            self.model.eval() 
            logger.info("✅ Load PhoBERT thành công!")
            
        except Exception as e:
            logger.error(f"❌ Lỗi khi load PhoBERT: {e}")

    def predict(self, text: str) -> float:
        if not self.model or not self.tokenizer:
            return 0.0
        
        if not text or len(str(text).strip()) == 0:
            return 0.0

        try:
            # 1. Tokenize văn bản
            inputs = self.tokenizer(
                text, 
                return_tensors="pt", 
                truncation=True, 
                max_length=256, 
                padding=True
            )

            # 2. Dự đoán (Forward pass)
            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = F.softmax(outputs.logits, dim=1)
            
            # 3. Xử lý kết quả (NEG, POS, NEU)
            # Model 'wonrax/phobert-base-vietnamese-sentiment' thường có thứ tự: [NEG, POS, NEU] hoặc [NEG, NEU, POS]
            # Cần kiểm tra config id2label của model cụ thể. 
            # Giả sử model này output 3 lớp: 0: Negative, 1: Positive, 2: Neutral
            
            scores = probs[0].tolist()
            neg_score = scores[0]
            pos_score = scores[1]
            # neu_score = scores[2] 

            # Tính điểm tổng hợp: Positive - Negative
            final_score = pos_score - neg_score
            
            return float(final_score)

        except Exception as e:
            logger.error(f"Lỗi dự đoán PhoBERT: {e}")
            return 0.0

# Wrapper function
def analyze_sentiment(text: str):
    model = CustomSentimentModel()
    score = model.predict(text)
    
    if score > 0.15:
        label = "Positive"
    elif score < -0.15:
        label = "Negative"
    else:
        label = "Neutral"
        
    return {"label": label, "score": score}