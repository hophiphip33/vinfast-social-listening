"""
Database connection and operations for VinFast Social Listening Platform
"""
from bson import ObjectId
import asyncio
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure
from loguru import logger

from backend.config.settings import settings

class DatabaseManager:
    """Async MongoDB connection manager"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
    
    async def connect(self):
        """Establish database connection"""
        try:
            self.client = AsyncIOMotorClient(settings.mongodb_url)
            self.database = self.client[settings.database_name]
            
            # Test the connection
            await self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {settings.database_name}")
            
            # Create indexes for better performance
            await self._create_indexes()
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    async def _create_indexes(self):
        """Create database indexes for optimal query performance"""
        try:
            # Posts collection indexes
            await self.database.posts.create_index([("platform", 1), ("published_at", -1)])
            await self.database.posts.create_index([("sentiment", 1)])
            await self.database.posts.create_index([("keywords", 1)])
            await self.database.posts.create_index([("collected_at", -1)])
            await self.database.posts.create_index([("source_url", 1)], unique=True, sparse=True)
            
            # Comments collection indexes
            await self.database.comments.create_index([("post_id", 1)])
            await self.database.comments.create_index([("published_at", -1)])
            await self.database.comments.create_index([("sentiment", 1)])
            
            # Analytics collection indexes
            await self.database.analytics.create_index([("start_date", 1), ("end_date", 1)])
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")
    
    def get_collection(self, collection_name: str):
        """Get a collection from the database"""
        if self.database is None:
            raise RuntimeError("Database not connected")
        return self.database[collection_name]

# Global database manager instance
db_manager = DatabaseManager()

class DatabaseOperations:
    """Database operations for the application"""
    
    @staticmethod
    async def insert_post(post_data: Dict[str, Any]) -> str:
        """Insert a new post"""
        try:
            collection = db_manager.get_collection("posts")
            result = await collection.insert_one(post_data)
            logger.debug(f"Inserted post with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error inserting post: {e}")
            raise
    
    @staticmethod
    async def insert_comment(comment_data: Dict[str, Any]) -> str:
        """Insert a new comment"""
        try:
            collection = db_manager.get_collection("comments")
            result = await collection.insert_one(comment_data)
            logger.debug(f"Inserted comment with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error inserting comment: {e}")
            raise
    
    @staticmethod
    async def get_posts(
        platform: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        sentiment: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve posts with filters"""
        try:
            collection = db_manager.get_collection("posts")
            query = {}
            
            if platform:
                query["platform"] = platform
            if sentiment:
                query["sentiment"] = sentiment
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter["$gte"] = start_date
                if end_date:
                    date_filter["$lte"] = end_date
                query["published_at"] = date_filter
            
            cursor = collection.find(query).sort("published_at", -1).limit(limit)
            posts = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string for JSON serialization
            for post in posts:
                post["_id"] = str(post["_id"])
            
            return posts
        except Exception as e:
            logger.error(f"Error retrieving posts: {e}")
            raise
    
    @staticmethod
    async def update_post_analysis(post_id: str, analysis_data: Dict[str, Any]):
        """Update post with sentiment analysis results"""
        try:
            collection = db_manager.get_collection("posts")
            await collection.update_one(
                {"_id": ObjectId(post_id)},
                {"$set": {**analysis_data, "is_processed": True}}
            )
            logger.debug(f"Updated analysis for post: {post_id}")
        except Exception as e:
            logger.error(f"Error updating post analysis: {e}")
            raise
    
    @staticmethod
    async def get_unprocessed_posts(limit: int = 50) -> List[Dict[str, Any]]:
        """Get posts that haven't been processed for sentiment analysis"""
        try:
            collection = db_manager.get_collection("posts")
            cursor = collection.find({"is_processed": False}).limit(limit)
            posts = await cursor.to_list(length=limit)
            
            for post in posts:
                post["_id"] = str(post["_id"])
            
            return posts
        except Exception as e:
            logger.error(f"Error getting unprocessed posts: {e}")
            raise
    
    @staticmethod
    async def get_post_by_id(post_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific post by ID"""
        try:
            collection = db_manager.get_collection("posts")
            post = await collection.find_one({"_id": ObjectId(post_id)})
            
            if post:
                post["_id"] = str(post["_id"])
                return post
            return None
        except Exception as e:
            logger.error(f"Error getting post by ID {post_id}: {e}")
            return None
    
    @staticmethod
    async def save_analytics_result(analytics_data: Dict[str, Any]) -> str:
        """Save analytics results"""
        try:
            collection = db_manager.get_collection("analytics")
            result = await collection.insert_one(analytics_data)
            logger.info(f"Saved analytics result with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error saving analytics result: {e}")
            raise
