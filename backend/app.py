# backend/app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
from sentiment.analyzer import SentimentAnalyzer

app = Flask(__name__)
CORS(app)

# Khởi tạo bộ phân tích cảm xúc (rule-based)
analyzer = SentimentAnalyzer()

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "message": "Backend is running"})

@app.route("/api/predict", methods=["POST"])
def predict():
    """
    Nhận JSON:
    { "text": "một câu tiếng Việt" }
    hoặc
    { "texts": ["câu 1", "câu 2", ...] }
    """
    data = request.get_json(silent=True) or {}
    if "texts" in data and isinstance(data["texts"], list):
        results = [analyzer.analyze_one(t) for t in data["texts"]]
        return jsonify({"results": results})
    
    text = data.get("text", "")
    result = analyzer.analyze_one(text)
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
