// MongoDB initialization script for VinFast Social Listening Platform

// Create database and user
db = db.getSiblingDB('vinfast_social_listening');

// Create collections with validation schemas
db.createCollection('posts', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['platform', 'content', 'published_at', 'collected_at'],
      properties: {
        platform: {
          bsonType: 'string',
          enum: ['facebook', 'tiktok', 'news']
        },
        content: {
          bsonType: 'string',
          minLength: 1
        },
        sentiment: {
          bsonType: 'string',
          enum: ['positive', 'negative', 'neutral']
        },
        published_at: {
          bsonType: 'date'
        },
        collected_at: {
          bsonType: 'date'
        }
      }
    }
  }
});

db.createCollection('comments', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['post_id', 'content', 'published_at', 'collected_at'],
      properties: {
        content: {
          bsonType: 'string',
          minLength: 1
        },
        sentiment: {
          bsonType: 'string',
          enum: ['positive', 'negative', 'neutral']
        }
      }
    }
  }
});

db.createCollection('analytics');
db.createCollection('data_sources');

// Create indexes
db.posts.createIndex({ platform: 1, published_at: -1 });
db.posts.createIndex({ sentiment: 1 });
db.posts.createIndex({ keywords: 1 });
db.posts.createIndex({ collected_at: -1 });
db.posts.createIndex({ source_url: 1 }, { unique: true, sparse: true });

db.comments.createIndex({ post_id: 1 });
db.comments.createIndex({ published_at: -1 });
db.comments.createIndex({ sentiment: 1 });

db.analytics.createIndex({ start_date: 1, end_date: 1 });

// Insert sample data sources
db.data_sources.insertMany([
  {
    name: 'VnExpress',
    platform: 'news',
    url: 'https://vnexpress.net',
    is_active: true,
    crawl_frequency: 'daily',
    max_posts: 50,
    created_at: new Date()
  },
  {
    name: 'VinFast Facebook',
    platform: 'facebook',
    url: 'https://facebook.com/VinFast',
    is_active: true,
    crawl_frequency: 'daily',
    max_posts: 30,
    created_at: new Date()
  },
  {
    name: 'VinFast TikTok',
    platform: 'tiktok',
    url: 'https://tiktok.com/tag/vinfast',
    is_active: true,
    crawl_frequency: 'daily',
    max_posts: 25,
    created_at: new Date()
  }
]);

print('VinFast Social Listening database initialized successfully!');
