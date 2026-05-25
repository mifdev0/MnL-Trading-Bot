"""
Position model - Trading positions
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, Text
from sqlalchemy.sql import func
from database import Base
from datetime import datetime, timezone

class Position(Base):
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    pair = Column(String(20), nullable=False, index=True)
    side = Column(String(5), nullable=False)  # LONG / SHORT
    entry_price = Column(Numeric(18, 8), nullable=False)
    sl_price = Column(Numeric(18, 8), nullable=False)
    tp_price = Column(Numeric(18, 8), nullable=False)
    quantity = Column(Numeric(18, 8), nullable=False)
    leverage = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="OPEN")  # OPEN / BE / TRAILING / CLOSED
    ai_reason = Column(Text)
    news_used = Column(Text)
    confidence = Column(Integer)
    pnl = Column(Numeric(18, 8), default=0)
    opened_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional fields for tracking
    order_id = Column(String(50), nullable=True)
    sl_order_id = Column(String(50), nullable=True)
    tp_order_id = Column(String(50), nullable=True)
    highest_price = Column(Numeric(18, 8), nullable=True)  # For trailing stop
    lowest_price = Column(Numeric(18, 8), nullable=True)   # For trailing stop
    partial_closed = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Position {self.pair} {self.side} @ {self.entry_price}>"
