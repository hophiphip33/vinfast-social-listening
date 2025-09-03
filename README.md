# VinFast Social Listening Platform 🚗📊

> **Graduation Project 2024** - Comprehensive Social Listening Platform for VinFast Brand Monitoring

## 📖 Project Overview

This is a complete social listening platform specifically designed to monitor and analyze public sentiment about **VinFast** across Vietnamese social media platforms and news sources. The project demonstrates advanced data collection, Vietnamese NLP, and real-time analytics capabilities.

### 🎯 Key Features

- **🔍 Multi-Source Data Collection**: Automated collection from news websites, Facebook, and TikTok
- **🧠 Vietnamese Sentiment Analysis**: Advanced NLP using PhoBERT and Vietnamese language models
- **📈 Real-time Analytics**: Comprehensive trend analysis and sentiment tracking
- **💻 Modern Dashboard**: React-based interface inspired by professional social listening tools
- **🏗️ Scalable Architecture**: Microservices with Docker and Kubernetes support
- **🇻🇳 Vietnamese Language Support**: Full end-to-end Vietnamese text processing

## 🏛️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   Processing    │    │   Frontend      │
│                 │    │                 │    │                 │
│ • News Sites    │───▶│ • Data Cleaning │───▶│ • React Dashboard│
│ • Facebook      │    │ • Sentiment ML  │    │ • Charts & Graphs│
│ • TikTok        │    │ • Analytics     │    │ • Vietnamese UI │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └──────────────────┬────┴───────────────────────┘
                           │
                    ┌─────────────────┐
                    │   Data Storage  │
                    │                 │
                    │ • MongoDB       │
                    │ • Redis Cache   │
                    │ • File Storage  │
                    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** (Recommended)
- **Python 3.9+** (For local development)
- **Node.js 16+** (For frontend development)
- **MongoDB** (Local or cloud)

### 1. Clone and Setup

\`\`\`bash
# Clone the repository
git clone <your-repo-url>
cd vinfast-social-listening

# Run setup script
chmod +x scripts/setup.sh
./scripts/setup.sh
\`\`\`

### 2. Configure Environment

\`\`\`bash
# Copy environment template
cp .env.example .env

# Edit configuration (important!)
nano .env
\`\`\`

### 3. Start with Docker (Recommended)

\`\`\`bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f
\`\`\`

### 4. Access the Platform

- **📊 Dashboard**: http://localhost:3000
- **🔧 API**: http://localhost:8000
- **📚 API Docs**: http://localhost:8000/docs

## 🛠️ Development Setup

### Backend Development

\`\`\`bash
# Start dependencies
docker-compose up mongodb redis -d

# Start backend for development
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install -r ../requirements.txt

# Run development server
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
\`\`\`

### Frontend Development

\`\`\`bash
# Install and start frontend
cd frontend
npm install
npm start

# Runs on http://localhost:3000
\`\`\`

### Alternative: Development Script

\`\`\`bash
# Start everything for development
chmod +x scripts/run-dev.sh
./scripts/run-dev.sh
\`\`\`

## 📊 Project Modules

### 1. Data Collection (`backend/collectors/`)

- **📰 News Collector**: Scrapes Vietnamese news websites (VnExpress, Tuổi Trẻ, etc.)
- **📘 Facebook Collector**: Collects public posts and comments using facebook-scraper
- **🎵 TikTok Collector**: Gathers public TikTok content and hashtags

**Key Technologies:**
- `requests`, `aiohttp` for HTTP requests
- `beautifulsoup4` for HTML parsing  
- `selenium` for dynamic content
- `facebook-scraper` for Facebook data
- `newspaper3k` for article extraction

### 2. Vietnamese NLP (`backend/processors/`)

- **🧠 Sentiment Analysis**: PhoBERT-based Vietnamese sentiment classification
- **🔤 Text Processing**: Vietnamese tokenization, keyword extraction
- **📝 Data Cleaning**: Specialized Vietnamese text preprocessing

**Key Technologies:**
- `transformers` with PhoBERT (`wonrax/phobert-base-vietnamese-sentiment`)
- `underthesea` for Vietnamese word segmentation
- `pyvi` for Vietnamese text processing
- `torch` for deep learning models

### 3. Analytics Engine (`backend/analytics/`)

- **📈 Trend Analysis**: Time-series sentiment tracking
- **🎯 Keyword Analysis**: Frequency and sentiment correlation
- **📋 Vietnamese Insights**: AI-generated summaries in Vietnamese
- **📊 Statistical Reports**: Comprehensive analytics

### 4. Database Layer (`backend/database/`)

- **🗄️ MongoDB Integration**: Document-based storage for social media data
- **⚡ Redis Caching**: Fast access to frequently used data
- **🔍 Efficient Queries**: Optimized indexes for large datasets

### 5. Web Dashboard (`frontend/`)

- **⚛️ React Frontend**: Modern, responsive dashboard
- **📊 Chart.js Integration**: Interactive data visualizations
- **🎨 Material-UI Design**: Professional, clean interface
- **🇻🇳 Vietnamese Support**: Full Vietnamese language interface

**Key Features:**
- Real-time metrics dashboard
- Interactive sentiment charts
- Keyword cloud visualization
- Post explorer with filtering
- Export functionality

## 📱 Dashboard Screenshots

The dashboard provides:
- **📊 Overview Dashboard**: Key metrics, sentiment distribution, trend charts
- **🔍 Analytics Page**: Detailed reports, keyword analysis, export options
- **⚙️ Data Collection**: Manage data sources, trigger collections
- **📋 Posts Explorer**: Browse, search, and analyze individual posts
- **⚙️ Settings**: System configuration and maintenance

## 🧪 Testing the Platform

### 1. Start Data Collection

\`\`\`bash
# Collect from all sources
curl -X POST http://localhost:8000/api/collect/all

# Or collect from specific sources
curl -X POST http://localhost:8000/api/collect/news
curl -X POST http://localhost:8000/api/collect/facebook
curl -X POST http://localhost:8000/api/collect/tiktok
\`\`\`

### 2. Process Sentiment Analysis

\`\`\`bash
# Process collected data for sentiment
curl -X POST http://localhost:8000/api/process/sentiment
\`\`\`

### 3. View Analytics

\`\`\`bash
# Get analytics overview
curl http://localhost:8000/api/analytics/overview?days=7

# Get real-time metrics
curl http://localhost:8000/api/analytics/real-time
\`\`\`

## 🚀 Deployment

### Docker Compose (Recommended)

\`\`\`bash
# Production deployment
docker-compose -f deployment/docker-compose.prod.yml up -d
\`\`\`

### Kubernetes

\`\`\`bash
# Deploy to Kubernetes
chmod +x scripts/deploy.sh
./scripts/deploy.sh
\`\`\`

### Manual Deployment

See `docs/deployment.md` for detailed deployment instructions.

## 📈 Performance Considerations

- **Async Processing**: All data collection and processing runs asynchronously
- **Background Tasks**: Celery workers handle heavy computations
- **Caching**: Redis caching for frequently accessed data
- **Database Optimization**: Proper indexing and query optimization
- **Resource Limits**: Docker resource constraints for production

## 🔒 Security & Privacy

- **Public Data Only**: Collects only publicly available social media content
- **Rate Limiting**: Respectful crawling with delays between requests
- **Data Privacy**: No personal information collection
- **Vietnamese Compliance**: Follows Vietnamese data protection guidelines

## 🎓 Educational Value

This graduation project demonstrates:

1. **Full-Stack Development**: Complete web application with modern technologies
2. **Data Engineering**: ETL pipelines, data processing, and storage
3. **Machine Learning**: Vietnamese NLP and sentiment analysis
4. **DevOps**: Containerization, orchestration, and deployment
5. **Vietnamese Technology**: Localized solution for Vietnamese market

## 📚 Documentation

- [Setup Guide](docs/setup.md)
- [API Documentation](http://localhost:8000/docs)
- [Development Guide](docs/development.md)
- [Deployment Guide](docs/deployment.md)
- [Vietnamese NLP Guide](docs/vietnamese-nlp.md)

## 🤝 Contributing

This is a graduation project, but suggestions and improvements are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **PhoBERT**: Vietnamese pre-trained language model
- **VinFast**: Subject of this social listening analysis
- **Vietnamese NLP Community**: Tools and resources for Vietnamese language processing
- **Open Source Libraries**: All the amazing libraries that made this project possible

---

**📧 Contact**: [Your Email]  
**🎓 Institution**: [Your University]  
**📅 Year**: 2024

> *This project is for educational purposes and demonstrates the capabilities of modern social listening technology applied to the Vietnamese market.*
