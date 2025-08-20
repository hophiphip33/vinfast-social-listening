from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

engine = create_engine("sqlite:///vinfast.db", future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    platform = Column(String(20), nullable=False)
    post_id = Column(String(100), unique=True)
    author = Column(String(100))
    content = Column(Text, nullable=False)
    published_date = Column(DateTime)
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    url = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed = relationship("ProcessedPost", back_populates="post", uselist=False)

class ProcessedPost(Base):
    __tablename__ = "processed_posts"
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id"))
    sentiment = Column(String(10))      # positive/neutral/negative
    sentiment_score = Column(Float)
    processed_at = Column(DateTime, default=datetime.utcnow)
    post = relationship("Post", back_populates="processed")

def init_db():
    Base.metadata.create_all(bind=engine)
