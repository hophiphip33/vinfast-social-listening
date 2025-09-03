# Getting Started with VinFast Social Listening Platform

## 🎯 Project Overview

This comprehensive guide will help you understand and run the **VinFast Social Listening Platform** - a graduation project that demonstrates advanced social media monitoring and Vietnamese sentiment analysis.

## 📋 What You'll Build

By the end of this setup, you'll have:

1. **🔍 Data Collection System** that automatically gathers VinFast-related content from:
   - Vietnamese news websites (VnExpress, Tuổi Trẻ, Thanh Niên)
   - Facebook public posts and comments
   - TikTok videos and hashtags

2. **🧠 Vietnamese AI Analysis** using:
   - PhoBERT for accurate Vietnamese sentiment analysis
   - Keyword extraction and topic modeling
   - Trend analysis and insights generation

3. **📊 Professional Dashboard** featuring:
   - Real-time sentiment monitoring
   - Interactive charts and visualizations
   - Vietnamese word clouds
   - Export and reporting capabilities

## ⚙️ Step-by-Step Setup

### Step 1: Prerequisites

Install the required software:

\`\`\`bash
# 1. Docker Desktop (Recommended)
# Download from https://www.docker.com/products/docker-desktop

# 2. Python 3.9+ (for local development)
# Download from https://www.python.org/downloads/

# 3. Node.js 16+ (for frontend development)  
# Download from https://nodejs.org/

# 4. Git (for version control)
# Download from https://git-scm.com/
\`\`\`

### Step 2: Project Setup

\`\`\`bash
# Clone your repository
git clone <your-github-repo-url>
cd vinfast-social-listening

# Run the automated setup script
chmod +x scripts/setup.sh
./scripts/setup.sh
\`\`\`

### Step 3: Configuration

\`\`\`bash
# Copy and edit environment variables
cp .env.example .env
nano .env  # Edit with your preferred editor

# Key configurations to update:
# - Database credentials
# - API keys (if using any paid services later)
# - Collection parameters (delay, max posts)
\`\`\`

### Step 4: Start the Platform

#### Option A: Docker Compose (Easiest)

\`\`\`bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
\`\`\`

#### Option B: Manual Development Setup

\`\`\`bash
# Terminal 1: Start MongoDB and Redis
docker-compose up mongodb redis

# Terminal 2: Start Backend API
cd backend
python -m venv venv
source venv/bin/activate
pip install -r ../requirements.txt
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3: Start Frontend
cd frontend
npm install
npm start
\`\`\`

### Step 5: Initial Data Collection

Once the platform is running:

1. **Open the Dashboard**: http://localhost:3000
2. **Go to "Thu thập dữ liệu"** (Data Collection) page
3. **Click "Thu thập tất cả"** (Collect All) to start gathering data
4. **Wait 5-10 minutes** for initial data collection
5. **Go back to Dashboard** to see results

## 📊 Using the Dashboard

### Main Dashboard Features

1. **📈 Overview Metrics**:
   - Total posts collected
   - Sentiment distribution (positive/negative/neutral)
   - Engagement statistics
   - Platform breakdown

2. **📊 Interactive Charts**:
   - Sentiment trends over time
   - Platform comparison
   - Word cloud of trending keywords

3. **🔍 Posts Explorer**:
   - Search through collected posts
   - Filter by platform, sentiment, date
   - View detailed post analysis

4. **⚙️ Settings & Management**:
   - Configure collection parameters
   - System status monitoring
   - Data export functionality

### Vietnamese Language Support

The platform is designed specifically for Vietnamese content:

- **✅ Vietnamese Sentiment Analysis**: Uses PhoBERT, the best Vietnamese language model
- **✅ Vietnamese Text Processing**: Proper tokenization and keyword extraction
- **✅ Vietnamese Interface**: All UI text and insights in Vietnamese
- **✅ Vietnamese Data Sources**: Focuses on Vietnamese news and social media

## 🧪 Testing the System

### Test Data Collection

\`\`\`bash
# Test news collection
curl -X POST http://localhost:8000/api/collect/news

# Test Facebook collection  
curl -X POST http://localhost:8000/api/collect/facebook

# Test sentiment analysis
curl -X POST http://localhost:8000/api/process/sentiment
\`\`\`

### Test API Endpoints

\`\`\`bash
# Get system health
curl http://localhost:8000/health

# Get analytics overview
curl http://localhost:8000/api/analytics/overview?days=7

# Search posts
curl "http://localhost:8000/api/search/posts?query=VinFast"
\`\`\`

### Test Manual Sentiment Analysis

\`\`\`bash
# Analyze Vietnamese text
curl -X POST http://localhost:8000/api/analyze/sentiment \\
  -H "Content-Type: application/json" \\
  -d '{"text":"VinFast VF8 là một chiếc xe điện tuyệt vời với thiết kế hiện đại"}'
\`\`\`

## 🔧 Common Issues & Solutions

### Issue: "No data available"
**Solution**: 
1. Start data collection from the dashboard
2. Wait 5-10 minutes for collection to complete
3. Refresh the page

### Issue: "Model not loading"
**Solution**:
1. Check internet connection (models download from HuggingFace)
2. Restart the backend service
3. Check logs: `docker-compose logs backend`

### Issue: "Database connection failed"
**Solution**:
1. Ensure MongoDB is running: `docker-compose ps`
2. Check MongoDB logs: `docker-compose logs mongodb`
3. Verify connection string in `.env`

### Issue: "Frontend won't load"
**Solution**:
1. Clear browser cache
2. Check if backend is running on port 8000
3. Restart frontend: `docker-compose restart frontend`

## 📈 Next Steps

Once you have the basic system running:

1. **📊 Analyze Results**: Look at the sentiment trends and insights
2. **🎛️ Customize Sources**: Add more news websites or social media pages
3. **🔧 Fine-tune Models**: Improve sentiment analysis accuracy
4. **📱 Enhance UI**: Add more visualizations and features
5. **🚀 Deploy**: Move to production environment

## 📚 Learning Resources

To understand the project better:

- **Vietnamese NLP**: Learn about Vietnamese language processing challenges
- **Social Listening**: Study commercial platforms like YouNetMedia
- **Sentiment Analysis**: Understand machine learning for text classification
- **React Dashboard**: Modern frontend development patterns
- **Docker & Kubernetes**: Container orchestration and deployment

## 🎓 For Your Graduation Project

This platform serves as a strong foundation for your graduation thesis:

- **📝 Technical Documentation**: Comprehensive code documentation
- **📊 Data Analysis**: Real Vietnamese social media data
- **🎯 Business Value**: Practical application for brand monitoring
- **🔬 Research Methodology**: Combines multiple data sources and ML techniques
- **📈 Scalable Solution**: Enterprise-ready architecture

## 🤝 Getting Help

If you encounter issues:

1. **Check the logs**: `docker-compose logs [service-name]`
2. **Review the code**: All code is well-commented
3. **Test individual components**: Use the API endpoints to debug
4. **Check Vietnamese text processing**: Ensure proper encoding and fonts

---

**Happy coding! 🚀 Chúc bạn thành công với đồ án tốt nghiệp!**
