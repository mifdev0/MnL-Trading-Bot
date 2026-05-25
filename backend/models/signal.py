"""
Signal model - AI trading signals
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.sql import func
from database import Base


class Signal(Base):
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    pair = Column(String(20), nullable=False, index=True)
    signal = Column(String(5), nullable=False)  # LONG / SHORT / SKIP
    confidence = Column(Integer, nullable=False)
    reason = Column(Text)
    executed = Column(Boolean, default=False)
    skip_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Additional signal data
    entry_price = Column(String(50), nullable=True)
    sl_price = Column(String(50), nullable=True)
    tp_price = Column(String(50), nullable=True)
    news_sentiment = Column(String(10), nullable=True)  # bullish / bearish / neutral
    technical_score = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<Signal {self.pair} {self.signal} ({self.confidence}%)>"
