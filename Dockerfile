# Sử dụng Python 3.9 Slim để nhẹ
FROM python:3.9-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Cài đặt các gói hệ thống cần thiết
# Thêm ffmpeg (cho yt-dlp) và git. Bỏ chromium để tiết kiệm 500MB RAM.
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy file thư viện
COPY requirements.txt .

# Cài đặt thư viện Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Tải dữ liệu NLTK (Cần thiết cho xử lý văn bản)
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# [QUAN TRỌNG] Tạo thư mục chứa model để tránh lỗi Permission
RUN mkdir -p /app/logs /app/ml-models /app/data

# Copy toàn bộ code vào
COPY backend/ ./backend/
# Nếu bạn có thư mục config riêng ở ngoài backend, hãy uncomment dòng dưới:
# COPY config/ ./config/

# Thiết lập biến môi trường
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Tạo user non-root để chạy (Bảo mật)
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Lệnh khởi chạy server
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]