"""
FastAPI Main Application for VinFast Social Listening Platform
RESTful API backend serving data to the dashboard frontend
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
from contextlib import asynccontextmanager

from backend.config.settings import settings
from backend.database.connection import db_manager, DatabaseOperations
from backend.collectors.news_collector import NewsCollector
from backend.processors.data_processor import data_processor
from backend.processors.vietnamese_sentiment import sentiment_analyzer
from backend.analytics.insights_engine import insights_engine
from backend.api.schemas import SentimentAnalysisRequest
from loguru import logger

# Lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    await db_manager.connect()
    await sentiment_analyzer.load_models()
    
    yield
    
    # Shutdown
    await db_manager.disconnect()

# Create FastAPI application
app = FastAPI(
    title="VinFast Social Listening Platform",
    description="Advanced social listening platform for VinFast sentiment analysis",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency
def get_db_ops() -> DatabaseOperations:
    return DatabaseOperations()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Data Collection Endpoints
@app.post("/api/collect/news")
async def collect_news_data(background_tasks: BackgroundTasks):
    """Trigger news data collection"""
    try:
        async def collect_news():
            async with NewsCollector() as collector:
                stats = await collector.collect_all_news()
                logger.info(f"News collection completed: {stats}")
        
        background_tasks.add_task(collect_news)
        
        return {
            "message": "Bắt đầu thu thập tin tức về VinFast",
            "status": "started",
            "estimated_duration": "2-5 phút"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting news collection: {str(e)}")



@app.post("/api/collect/all")
async def collect_all_data(background_tasks: BackgroundTasks):
    """Trigger data collection from all sources"""
    try:
        async def collect_all():
            # Collect from all sources
            async with NewsCollector() as news_collector:
                news_stats = await news_collector.collect_all_news()
            
            
            
            # Process collected data
            processing_stats = await data_processor.process_unprocessed_data()
            
            logger.info(f"Full collection completed - News: {news_stats}, Processing: {processing_stats}")
        
        background_tasks.add_task(collect_all)
        
        return {
            "message": "Bắt đầu thu thập dữ liệu từ tất cả các nguồn",
            "status": "started",
            "estimated_duration": "10-20 phút"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting full collection: {str(e)}")

# Data Processing Endpoints
@app.post("/api/process/sentiment")
async def process_sentiment_analysis(background_tasks: BackgroundTasks):
    """Process unprocessed data for sentiment analysis"""
    try:
        async def process_data():
            stats = await data_processor.process_unprocessed_data()
            logger.info(f"Data processing completed: {stats}")
        
        background_tasks.add_task(process_data)
        
        return {
            "message": "Bắt đầu phân tích tình cảm cho dữ liệu mới",
            "status": "started"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting sentiment processing: {str(e)}")

# Analytics Endpoints
@app.get("/api/analytics/overview")
async def get_analytics_overview(
    days: int = Query(7, description="Number of days to analyze"),
    db_ops: DatabaseOperations = Depends(get_db_ops)
):
    """Get analytics overview for the dashboard"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        report = await insights_engine.generate_comprehensive_report(start_date, end_date)
        
        return {
            "success": True,
            "data": report,
            "message": f"Báo cáo phân tích cho {days} ngày gần nhất"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating overview: {str(e)}")

@app.get("/api/analytics/real-time")
async def get_real_time_metrics():
    """Get real-time metrics for dashboard widgets"""
    try:
        metrics = await insights_engine.get_real_time_metrics()
        return {
            "success": True,
            "data": metrics,
            "message": "Số liệu thời gian thực"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting real-time metrics: {str(e)}")

@app.get("/api/analytics/sentiment-trends")
async def get_sentiment_trends(
    days: int = Query(30, description="Number of days for trend analysis"),
    interval: str = Query("daily", description="Trend interval: daily, weekly")
):
    """Get sentiment trends over time"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        trends = await data_processor.generate_sentiment_trends(start_date, end_date, interval)
        
        return {
            "success": True,
            "data": trends,
            "message": f"Xu hướng tình cảm trong {days} ngày qua"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting sentiment trends: {str(e)}")

@app.get("/api/analytics/keywords")
async def get_keyword_analysis(
    days: int = Query(7, description="Number of days to analyze"),
    limit: int = Query(50, description="Number of top keywords to return")
):
    """Get keyword frequency analysis"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        keywords = await data_processor.generate_keyword_frequency(start_date, end_date, limit)
        
        return {
            "success": True,
            "data": keywords,
            "message": f"Phân tích từ khóa cho {days} ngày gần nhất"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting keyword analysis: {str(e)}")

# Data Retrieval Endpoints
@app.get("/api/posts")
async def get_posts(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment"),
    days: int = Query(7, description="Number of days to look back"),
    limit: int = Query(100, description="Maximum number of posts"),
    db_ops: DatabaseOperations = Depends(get_db_ops)
):
    """Get posts with filtering options"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        posts = await db_ops.get_posts(
            platform=platform,
            sentiment=sentiment,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            limit=limit
        )
        
        return {
            "success": True,
            "data": posts,
            "total": len(posts),
            "filters": {
                "platform": platform,
                "sentiment": sentiment,
                "days": days
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving posts: {str(e)}")

@app.get("/api/posts/{post_id}")
async def get_post_details(post_id: str, db_ops: DatabaseOperations = Depends(get_db_ops)):
    """Get detailed information about a specific post"""
    try:
        # This would need to be implemented in DatabaseOperations
        post = await db_ops.get_post_by_id(post_id)
        
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        return {
            "success": True,
            "data": post
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving post details: {str(e)}")

# Dashboard Endpoints
@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get key statistics for dashboard"""
    try:
        # Get real-time metrics
        real_time = await insights_engine.get_real_time_metrics()
        
        # Get overview for last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        overview = await insights_engine.generate_comprehensive_report(start_date, end_date)
        
        return {
            "success": True,
            "data": {
                "real_time": real_time,
                "weekly_overview": {
                    "basic_statistics": overview.get("basic_statistics", {}),
                    "sentiment_analysis": overview.get("sentiment_analysis", {}),
                    "platform_breakdown": overview.get("platform_breakdown", {})
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dashboard stats: {str(e)}")

@app.get("/api/dashboard/wordcloud")
async def get_wordcloud_data(
    days: int = Query(7, description="Number of days for wordcloud"),
    limit: int = Query(100, description="Number of keywords")
):
    """Get data for word cloud visualization"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        keywords = await data_processor.generate_keyword_frequency(start_date, end_date, limit)
        
        # Format for word cloud
        wordcloud_data = [
            {"text": kw["keyword"], "value": kw["count"], "sentiment": kw.get("sentiment_category", "neutral")}
            for kw in keywords
        ]
        
        return {
            "success": True,
            "data": wordcloud_data,
            "message": f"Dữ liệu word cloud cho {days} ngày gần nhất"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting wordcloud data: {str(e)}")

# Manual Sentiment Analysis Endpoint
@app.post("/api/analyze/sentiment")
async def analyze_text_sentiment(request: SentimentAnalysisRequest):
    """Analyze sentiment of provided text"""
    try:
        result = await sentiment_analyzer.analyze_sentiment(request.text)
        keywords = sentiment_analyzer.extract_keywords(request.text)
        
        return {
            "success": True,
            "data": {
                **result,
                "keywords": keywords,
                "original_text": request.text
            },
            "message": "Phân tích tình cảm hoàn thành"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing sentiment: {str(e)}")

# Export Endpoints
@app.get("/api/export/report")
async def export_report(
    days: int = Query(30, description="Number of days for the report"),
    format: str = Query("json", description="Export format: json, csv")
):
    """Export analytics report"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        report = await insights_engine.generate_comprehensive_report(start_date, end_date)
        
        if format.lower() == "csv":
            # Convert to CSV format (implement as needed)
            return JSONResponse(
                content={"message": "CSV export not yet implemented"},
                status_code=501
            )
        
        return {
            "success": True,
            "data": report,
            "export_info": {
                "format": format,
                "generated_at": datetime.now().isoformat(),
                "period": f"{days} days"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting report: {str(e)}")

# System Status Endpoints
@app.get("/api/system/status")
async def get_system_status():
    """Get system status and health"""
    try:
        # Check database connection
        try:
            await db_manager.client.admin.command('ping')
            db_status = "connected"
        except:
            db_status = "disconnected"
        
        # Check model status
        model_status = "loaded" if sentiment_analyzer.is_loaded else "not_loaded"
        
        return {
            "success": True,
            "data": {
                "database": db_status,
                "sentiment_model": model_status,
                "api_version": "1.0.0",
                "uptime": "active",
                "last_collection": "N/A",  # Would track this in production
                "processed_posts_today": 0  # Would calculate this
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Error checking system status"
        }

# Search Endpoints  
@app.get("/api/search/posts")
async def search_posts(
    query: str = Query(..., description="Search query"),
    platform: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    limit: int = Query(50, description="Maximum results"),
    db_ops: DatabaseOperations = Depends(get_db_ops)
):
    """Search posts by content"""
    try:
        # This would implement text search in the database
        # For now, return filtered results
        posts = await db_ops.get_posts(
            platform=platform,
            sentiment=sentiment,
            limit=limit
        )
        
        # Simple text filtering (in production, use database text search)
        if query:
            query_lower = query.lower()
            filtered_posts = [
                post for post in posts
                if query_lower in (post.get("content", "").lower() + " " + 
                                 (post.get("title", "") or "").lower())
            ]
        else:
            filtered_posts = posts
        
        return {
            "success": True,
            "data": filtered_posts,
            "total": len(filtered_posts),
            "query": query
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching posts: {str(e)}")

# Admin Endpoints
@app.delete("/api/admin/reset-data")
async def reset_all_data():
    """Reset all collected data (for development/testing)"""
    try:
        # Clear collections
        await db_manager.database.posts.delete_many({})
        await db_manager.database.comments.delete_many({})
        await db_manager.database.analytics.delete_many({})
        
        return {
            "success": True,
            "message": "Đã xóa tất cả dữ liệu thu thập",
            "warning": "Thao tác này không thể hoàn tác"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting data: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower()
    )
@app.get("/api/system/status")
async def get_system_status():
    ...
