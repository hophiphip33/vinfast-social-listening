"""
Vietnamese Sentiment Analysis for VinFast Social Listening Platform
Uses PhoBERT and other Vietnamese NLP models for accurate sentiment classification
"""

import asyncio
import re
from typing import List, Dict, Any, Tuple, Optional
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import numpy as np
from underthesea import word_tokenize, pos_tag
from pyvi import ViTokenizer
from loguru import logger

from backend.config.settings import settings

class VietnameseSentimentAnalyzer:
    """Vietnamese sentiment analysis using pre-trained models"""
    
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.sentiment_pipeline = None
        self.is_loaded = False
        
        # Vietnamese text preprocessing patterns
        self.emoji_pattern = re.compile(
            r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+'
        )
        
        # Vietnamese stopwords
        self.vietnamese_stopwords = {
            'và', 'của', 'cho', 'với', 'từ', 'theo', 'như', 'để', 'trong', 'về',
            'là', 'có', 'được', 'sẽ', 'đã', 'đang', 'khi', 'nếu', 'mà', 'này',
            'đó', 'nó', 'họ', 'chúng', 'tôi', 'bạn', 'anh', 'chị', 'em',
            'thì', 'cũng', 'đều', 'rất', 'lắm', 'nhiều', 'ít', 'hơn', 'nhất'
        }
    
    async def load_models(self):
        """Load Vietnamese sentiment analysis models"""
        try:
            logger.info("Loading Vietnamese sentiment analysis models...")
            
            # Load PhoBERT for sentiment analysis
            model_name = "wonrax/phobert-base-vietnamese-sentiment"
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            
            # Create sentiment analysis pipeline
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1
            )
            
            self.is_loaded = True
            logger.info("Vietnamese sentiment models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading sentiment models: {e}")
            # Fallback to a simpler approach
            await self._load_fallback_model()
    
    async def _load_fallback_model(self):
        """Load a fallback model if PhoBERT is not available"""
        try:
            logger.info("Loading fallback sentiment model...")
            
            # Use a lighter Vietnamese sentiment model or TextBlob
            from textblob import TextBlob
            
            self.is_loaded = True
            logger.info("Fallback sentiment model loaded")
            
        except Exception as e:
            logger.error(f"Error loading fallback model: {e}")
            self.is_loaded = False
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess Vietnamese text for sentiment analysis"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Handle emojis (convert to sentiment indicators)
        emoji_sentiment_map = {
            '😍': ' tích_cực ',
            '😊': ' tích_cực ',
            '😀': ' tích_cực ',
            '👍': ' tích_cực ',
            '❤️': ' tích_cực ',
            '😢': ' tiêu_cực ',
            '😭': ' tiêu_cực ',
            '😠': ' tiêu_cực ',
            '😡': ' tiêu_cực ',
            '👎': ' tiêu_cực '
        }
        
        for emoji, sentiment in emoji_sentiment_map.items():
            text = text.replace(emoji, sentiment)
        
        # Remove remaining emojis
        text = self.emoji_pattern.sub('', text)
        
        # Vietnamese word segmentation using PyVi
        try:
            text = ViTokenizer.tokenize(text)
        except:
            pass  # Continue without tokenization if error
        
        # Remove URLs
        text = re.sub(r'http\S+|www\.\S+', '', text)
        
        # Remove special characters but keep Vietnamese characters
        text = re.sub(r'[^\w\s\u00C0-\u1EF9]', ' ', text)
        
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """Extract important keywords from Vietnamese text"""
        if not text:
            return []
        
        try:
            # Tokenize and POS tagging using underthesea
            tokens = word_tokenize(text)
            pos_tags = pos_tag(text)
            
            # Extract nouns and adjectives (important for sentiment)
            keywords = []
            for word, pos in pos_tags:
                if pos in ['N', 'A'] and len(word) > 2:  # Nouns and Adjectives
                    if word.lower() not in self.vietnamese_stopwords:
                        keywords.append(word.lower())
            
            # Count frequency and return top keywords
            from collections import Counter
            keyword_counts = Counter(keywords)
            
            return [word for word, count in keyword_counts.most_common(top_k)]
            
        except Exception as e:
            logger.warning(f"Error extracting keywords: {e}")
            # Simple fallback - split and filter
            words = text.split()
            filtered_words = [
                word for word in words 
                if len(word) > 2 and word.lower() not in self.vietnamese_stopwords
            ]
            return filtered_words[:top_k]
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of Vietnamese text"""
        if not self.is_loaded:
            await self.load_models()
        
        if not text.strip():
            return {
                "sentiment": "neutral",
                "confidence_score": 0.0,
                "sentiment_score": 0.0
            }
        
        try:
            # Preprocess text
            processed_text = self.preprocess_text(text)
            
            if len(processed_text) < 5:  # Too short for meaningful analysis
                return {
                    "sentiment": "neutral",
                    "confidence_score": 0.0,
                    "sentiment_score": 0.0
                }
            
            # Truncate if too long
            if len(processed_text) > settings.max_sequence_length:
                processed_text = processed_text[:settings.max_sequence_length]
            
            # Analyze sentiment using PhoBERT
            if self.sentiment_pipeline:
                result = self.sentiment_pipeline(processed_text)[0]
                
                # Map labels to our standard format
                label_mapping = {
                    "POSITIVE": "positive",
                    "NEGATIVE": "negative", 
                    "NEUTRAL": "neutral",
                    "POS": "positive",
                    "NEG": "negative",
                    "NEU": "neutral"
                }
                
                sentiment_label = label_mapping.get(result['label'].upper(), "neutral")
                confidence = float(result['score'])
                
                # Convert to sentiment score (-1 to 1)
                if sentiment_label == "positive":
                    sentiment_score = confidence
                elif sentiment_label == "negative":
                    sentiment_score = -confidence
                else:
                    sentiment_score = 0.0
                
                return {
                    "sentiment": sentiment_label,
                    "confidence_score": confidence,
                    "sentiment_score": sentiment_score
                }
            
            else:
                # Fallback sentiment analysis
                return await self._fallback_sentiment_analysis(processed_text)
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {
                "sentiment": "neutral",
                "confidence_score": 0.0,
                "sentiment_score": 0.0
            }
    
    async def _fallback_sentiment_analysis(self, text: str) -> Dict[str, Any]:
        """Fallback sentiment analysis using keyword-based approach"""
        try:
            # Vietnamese positive and negative words
            positive_words = {
                'tốt', 'hay', 'đẹp', 'tuyệt', 'xuất sắc', 'tuyệt vời', 'ưng ý', 
                'hài lòng', 'thích', 'yêu', 'tán thành', 'ủng hộ', 'khen',
                'chất lượng', 'hoàn hảo', 'ấn tượng', 'tích cực', 'mạnh mẽ'
            }
            
            negative_words = {
                'tệ', 'xấu', 'dở', 'kém', 'thất vọng', 'ghét', 'chán', 'tức giận',
                'phản đối', 'chê', 'bực', 'tồi tệ', 'thảm họa', 'tiêu cực',
                'không thích', 'phàn nàn', 'khiếu nại', 'lừa đảo', 'rác'
            }
            
            words = text.lower().split()
            positive_count = sum(1 for word in words if word in positive_words)
            negative_count = sum(1 for word in words if word in negative_words)
            
            total_sentiment_words = positive_count + negative_count
            
            if total_sentiment_words == 0:
                return {"sentiment": "neutral", "confidence_score": 0.5, "sentiment_score": 0.0}
            
            sentiment_score = (positive_count - negative_count) / max(total_sentiment_words, 1)
            confidence = min(total_sentiment_words / 10, 1.0)  # Max confidence of 1.0
            
            if sentiment_score > 0.1:
                sentiment = "positive"
            elif sentiment_score < -0.1:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            return {
                "sentiment": sentiment,
                "confidence_score": confidence,
                "sentiment_score": sentiment_score
            }
            
        except Exception as e:
            logger.error(f"Error in fallback sentiment analysis: {e}")
            return {"sentiment": "neutral", "confidence_score": 0.0, "sentiment_score": 0.0}
    
    async def batch_analyze_sentiment(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Analyze sentiment for multiple texts efficiently"""
        if not self.is_loaded:
            await self.load_models()
        
        results = []
        
        for text in texts:
            result = await self.analyze_sentiment(text)
            results.append(result)
            
            # Small delay to prevent overwhelming the model
            await asyncio.sleep(0.1)
        
        logger.info(f"Completed batch sentiment analysis for {len(texts)} texts")
        return results
    
    def get_sentiment_distribution(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate sentiment distribution statistics"""
        sentiments = [result["sentiment"] for result in results]
        scores = [result["sentiment_score"] for result in results]
        
        distribution = {
            "positive": sentiments.count("positive"),
            "negative": sentiments.count("negative"),
            "neutral": sentiments.count("neutral"),
            "total": len(sentiments)
        }
        
        distribution["positive_ratio"] = distribution["positive"] / max(distribution["total"], 1)
        distribution["negative_ratio"] = distribution["negative"] / max(distribution["total"], 1)
        distribution["neutral_ratio"] = distribution["neutral"] / max(distribution["total"], 1)
        
        distribution["avg_sentiment_score"] = np.mean(scores) if scores else 0.0
        distribution["sentiment_std"] = np.std(scores) if len(scores) > 1 else 0.0
        
        return distribution

# Global sentiment analyzer instance
sentiment_analyzer = VietnameseSentimentAnalyzer()

# Usage example
async def main():
    """Example usage"""
    analyzer = VietnameseSentimentAnalyzer()
    
    # Test texts in Vietnamese
    test_texts = [
        "VinFast VF8 thật tuyệt vời, xe điện đẹp và chất lượng cao",
        "Tôi thất vọng về chất lượng xe VinFast, có nhiều lỗi",
        "VinFast là thương hiệu xe hơi của Việt Nam"
    ]
    
    for text in test_texts:
        result = await analyzer.analyze_sentiment(text)
        keywords = analyzer.extract_keywords(text)
        
        print(f"Text: {text}")
        print(f"Sentiment: {result['sentiment']} (score: {result['sentiment_score']:.2f}, confidence: {result['confidence_score']:.2f})")
        print(f"Keywords: {keywords}")
        print("-" * 80)

if __name__ == "__main__":
    asyncio.run(main())
