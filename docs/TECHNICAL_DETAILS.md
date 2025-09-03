# Technical Implementation Details

## 🏗️ System Architecture

### Backend Architecture (FastAPI + Python)

```
vinfast-social-listening/backend/
├── api/                    # REST API endpoints
│   ├── main.py            # FastAPI application
│   └── schemas.py         # Pydantic models
├── collectors/             # Data collection modules
│   ├── news_collector.py  # News websites scraping
│   ├── facebook_collector.py # Facebook public data
│   └── tiktok_collector.py   # TikTok public content
├── processors/             # Data processing pipeline
│   ├── vietnamese_sentiment.py # Vietnamese NLP
│   └── data_processor.py      # ETL pipeline
├── analytics/              # Analytics engine
│   └── insights_engine.py  # Statistics and insights
├── database/               # Database layer
│   ├── models.py          # Data models
│   └── connection.py      # MongoDB operations
└── tasks/                  # Background tasks
    ├── worker.py          # Celery workers
    └── scheduler.py       # Automated scheduling
```

### Frontend Architecture (React + Material-UI)

```
vinfast-social-listening/frontend/src/
├── components/             # Reusable UI components
│   ├── Navbar.js          # Top navigation
│   ├── Sidebar.js         # Side navigation
│   ├── StatCard.js        # Metrics cards
│   ├── RecentPosts.js     # Post listings
│   ├── KeyInsights.js     # AI insights
│   └── charts/            # Chart components
├── pages/                  # Main application pages
│   ├── Dashboard.js       # Overview dashboard
│   ├── Analytics.js       # Detailed analytics
│   ├── DataCollection.js  # Collection management
│   ├── PostsExplorer.js   # Posts browser
│   └── Settings.js        # System settings
├── services/               # API integration
│   └── api.js            # HTTP client and utilities
├── hooks/                  # Custom React hooks
└── utils/                  # Utility functions
```

## 🔍 Data Collection Implementation

### 1. News Collection Strategy

**Target Sources**: Vietnamese news websites with high credibility
- VnExpress (vnexpress.net)
- Tuổi Trẻ (tuoitre.vn)
- Thanh Niên (thanhnien.vn)
- VietNamNet (vietnamnet.vn)

**Collection Methods**:
```python
# RSS Feed Collection
async def collect_from_rss(source):
    - Parse RSS feeds for recent articles
    - Filter VinFast-related content
    - Extract full article text using newspaper3k
    - Store with metadata and timestamps

# Search-based Collection  
async def collect_from_search(source):
    - Query search endpoints with VinFast keywords
    - Extract article links from search results
    - Process articles for content and sentiment
    - Deduplicate based on URL
```

**Keywords Used**:
```python
vinfast_keywords = [
    "vinfast", "vin fast", "xe vinfast", "ô tô vinfast",
    "xe điện vinfast", "vf8", "vf9", "vf5", "fadil",
    "lux a2.0", "lux sa2.0", "vingroup", "phạm nhật vượng"
]
```

### 2. Facebook Collection Strategy

**Approach**: Public data only using facebook-scraper library
```python
# Public Page Collection
async def collect_from_page(page_name):
    - Access public Facebook pages
    - Extract posts, engagement metrics
    - Collect public comments
    - Filter VinFast-related content only
```

**Target Pages**:
- VinFast official pages
- Vietnamese automotive communities  
- Car review pages
- Technology news pages

**Limitations**: 
- Public content only (no private posts)
- Rate limiting to respect platform policies
- Content filtering to stay focused on VinFast

### 3. TikTok Collection Strategy

**Method**: Web scraping of public content
```python
# Hashtag Collection
async def scrape_hashtag_posts(hashtag):
    - Access public hashtag pages
    - Extract video metadata and descriptions
    - Collect engagement metrics
    - Process Vietnamese text content

# Search Collection
async def search_public_videos(keyword):
    - Use TikTok's public search interface
    - Extract video information
    - Filter VinFast-related content
```

**Target Hashtags**:
```python
hashtags = [
    "#vinfast", "#vf8", "#vf9", "#vf5",
    "#xevinfast", "#otosaigon", "#xedien"
]
```

## 🧠 Vietnamese Sentiment Analysis

### PhoBERT Implementation

**Model**: `wonrax/phobert-base-vietnamese-sentiment`
- Pre-trained on Vietnamese social media text
- Fine-tuned for sentiment classification
- Handles Vietnamese-specific language patterns

```python
# Sentiment Analysis Pipeline
async def analyze_sentiment(text):
    1. Text preprocessing (Vietnamese-specific)
    2. Tokenization using Vietnamese word segmentation
    3. PhoBERT inference
    4. Confidence scoring and result mapping
```

### Vietnamese Text Processing

**Preprocessing Steps**:
```python
def preprocess_text(text):
    1. Vietnamese character normalization
    2. Emoji sentiment mapping
    3. URL and special character removal
    4. Word segmentation using PyVi
    5. Stopword filtering (Vietnamese)
```

**Keyword Extraction**:
```python
def extract_keywords(text):
    1. Vietnamese POS tagging (underthesea)
    2. Extract nouns and adjectives
    3. Filter Vietnamese stopwords
    4. Frequency counting and ranking
```

### Fallback Analysis

For cases where PhoBERT is unavailable:
```python
# Rule-based Vietnamese sentiment
positive_words = {
    'tốt', 'hay', 'đẹp', 'tuyệt', 'xuất sắc', 
    'tuyệt vời', 'ưng ý', 'hài lòng', 'thích'
}

negative_words = {
    'tệ', 'xấu', 'dở', 'kém', 'thất vọng', 
    'ghét', 'chán', 'tức giận', 'phản đối'
}
```

## 📊 Analytics Engine

### Real-time Metrics
```python
# Live dashboard metrics updated every minute
- Total posts in last 24 hours
- Sentiment distribution
- Platform breakdown
- Trending keywords
- Average engagement rates
```

### Comprehensive Reports
```python
# Generated analytics include:
- Basic statistics (posts, engagement, reach)
- Sentiment analysis (distribution, trends, scores)
- Platform comparison (Facebook vs TikTok vs News)
- Keyword frequency and sentiment correlation
- Topic modeling (product, business, technology themes)
- Temporal trends (daily, weekly patterns)
- Vietnamese insights (AI-generated summaries)
```

### Insight Generation

AI-powered Vietnamese insights:
```python
def generate_vietnamese_summary():
    - Analyze sentiment trends
    - Identify key topics and keywords
    - Generate business intelligence in Vietnamese
    - Provide actionable recommendations
```

## 🗄️ Database Design

### MongoDB Schema

**Posts Collection**:
```javascript
{
  _id: ObjectId,
  platform: "facebook" | "tiktok" | "news",
  source_url: String,
  source_name: String,
  title: String?,
  content: String,
  author: String?,
  likes_count: Number,
  shares_count: Number,
  comments_count: Number,
  views_count: Number,
  published_at: Date,
  collected_at: Date,
  sentiment: "positive" | "negative" | "neutral",
  sentiment_score: Number,    // -1.0 to 1.0
  confidence_score: Number,   // 0.0 to 1.0
  keywords: [String],
  topics: [String],
  language: "vi",
  is_processed: Boolean
}
```

**Comments Collection**:
```javascript
{
  _id: ObjectId,
  post_id: ObjectId,
  parent_comment_id: ObjectId?,
  content: String,
  author: String?,
  likes_count: Number,
  replies_count: Number,
  published_at: Date,
  collected_at: Date,
  sentiment: String?,
  sentiment_score: Number?,
  confidence_score: Number?,
  language: "vi",
  is_processed: Boolean
}
```

**Analytics Collection**:
```javascript
{
  _id: ObjectId,
  start_date: Date,
  end_date: Date,
  basic_statistics: Object,
  sentiment_analysis: Object,
  platform_breakdown: Object,
  keyword_analysis: Object,
  topic_analysis: Object,
  vietnamese_summary: String,
  key_insights: [String],
  created_at: Date
}
```

### Database Indexes

Optimized for query performance:
```javascript
// Posts indexes
db.posts.createIndex({ platform: 1, published_at: -1 })
db.posts.createIndex({ sentiment: 1 })
db.posts.createIndex({ keywords: 1 })
db.posts.createIndex({ collected_at: -1 })
db.posts.createIndex({ source_url: 1 }, { unique: true })

// Comments indexes  
db.comments.createIndex({ post_id: 1 })
db.comments.createIndex({ published_at: -1 })
db.comments.createIndex({ sentiment: 1 })
```

## 🔄 Background Processing

### Celery Task Queue

**Workers Handle**:
- Data collection tasks (async, retryable)
- Sentiment analysis processing (batch processing)
- Analytics report generation
- Data cleanup and maintenance

**Task Types**:
```python
@app.task(bind=True, max_retries=3)
def collect_news_task():
    # Collect news articles with retry logic

@app.task(bind=True, max_retries=3) 
def process_sentiment_task(batch_size=50):
    # Batch sentiment analysis processing

@app.task
def full_collection_pipeline():
    # Orchestrate complete collection workflow
```

### Automated Scheduling

**Schedule Configuration**:
```python
# Daily full collection at 8 AM Vietnam time
schedule.every().day.at("08:00").do(daily_collection)

# Process sentiment every 2 hours
schedule.every(2).hours.do(sentiment_processing)

# Collect news every 4 hours  
schedule.every(4).hours.do(news_collection)

# Collect social media every 6 hours
schedule.every(6).hours.do(social_collection)
```

## 🎨 Frontend Implementation

### React Architecture

**State Management**: React Query for server state
```javascript
// Automatic caching, background updates, error handling
const { data, isLoading, error } = useQuery({
  queryKey: ['analytics', timeRange],
  queryFn: () => fetchAnalyticsOverview(timeRange),
  refetchInterval: 60000  // Auto-refresh
});
```

**UI Components**: Material-UI with Vietnamese customization
```javascript
// Vietnamese font support
const theme = createTheme({
  typography: {
    fontFamily: '"Inter", "Roboto", "Arial", sans-serif'
  }
});
```

### Chart Visualizations

**Chart.js Integration**:
```javascript
// Sentiment Distribution (Doughnut Chart)
- Interactive pie chart showing positive/negative/neutral ratios
- Vietnamese labels and tooltips
- Custom colors for sentiment categories

// Trend Charts (Line Chart)
- Time series sentiment analysis
- Multiple datasets (positive, negative, neutral counts)
- Vietnamese date formatting

// Platform Breakdown (Bar Chart)  
- Comparison across platforms
- Engagement metrics visualization

// Word Cloud
- Vietnamese keyword visualization
- Sentiment-based coloring
- Interactive word selection
```

## 🚀 Deployment Architecture

### Docker Setup

**Multi-stage builds** for optimized images:
```dockerfile
# Backend: Python + ML models
FROM python:3.9-slim
- Install Vietnamese NLP dependencies
- Download PhoBERT models
- Optimize for production

# Frontend: Node.js build + Nginx serve
FROM node:18-alpine as build
FROM nginx:alpine as production
- Build optimized React bundle
- Configure nginx for SPA routing
```

### Kubernetes Deployment

**Service Mesh**:
```yaml
# MongoDB StatefulSet with persistent storage
# Redis Deployment for caching
# Backend Deployment with horizontal scaling
# Frontend Deployment with load balancing
# Nginx Ingress for traffic management
```

### Monitoring Stack

**Integrated Monitoring**:
- **Prometheus**: Metrics collection
- **Grafana**: Dashboard visualization
- **ELK Stack**: Log aggregation (from your existing setup)
- **Health checks**: Automated service monitoring

## 🔒 Security Considerations

### Data Privacy
- **Public data only**: No private social media content
- **Vietnamese law compliance**: Follows local regulations
- **Rate limiting**: Respectful data collection
- **Data anonymization**: Remove personal identifiers

### Application Security
- **Input validation**: All user inputs sanitized
- **API rate limiting**: Prevent abuse
- **HTTPS enforcement**: Secure data transmission
- **Authentication**: Secure admin interfaces

## 🎓 Educational Outcomes

This project demonstrates mastery of:

1. **Full-Stack Development**
   - Modern web technologies (React, FastAPI)
   - Database design and optimization
   - RESTful API development

2. **Data Engineering** 
   - ETL pipeline design
   - Real-time data processing
   - Background task management

3. **Machine Learning**
   - Vietnamese NLP implementation
   - Sentiment analysis techniques
   - Model deployment and scaling

4. **DevOps & Deployment**
   - Containerization with Docker
   - Kubernetes orchestration
   - CI/CD pipeline setup

5. **Vietnamese Technology Adaptation**
   - Localized NLP solutions
   - Cultural and linguistic considerations
   - Vietnamese market applications

---

This technical documentation provides the foundation for understanding and extending the VinFast Social Listening Platform. Use it as a reference for your graduation project documentation and future development.
