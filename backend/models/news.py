"""
News model - Processed crypto news
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ARRAY
from sqlalchemy.sql import func
from database import Base


class News(Base):
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    source = Column(String(50), nullable=False)
    sentiment = Column(String(10), nullable=False)  # bullish / bearish / neutral
    coins = Column(ARRAY(String), nullable=True)
    url = Column(Text, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=False)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Additional fields
    content = Column(Text, nullable=True)
    processed = Column(String(1), default='N')  # Y/N flag
    
    def __repr__(self):
        return f"<News {self.title[:50]}... ({self.sentiment})>"
