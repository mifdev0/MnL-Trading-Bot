"""
Signals router - AI signals endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.signal import Signal

router = APIRouter(prefix="/api/signals", tags=["signals"])


@router.get("")
async def get_signals(limit: int = 20, db: Session = Depends(get_db)):
    """Get AI signals"""
    try:
        signals = db.query(Signal).order_by(
            Signal.created_at.desc()
        ).limit(limit).all()
        
        return {
            "success": True,
            "data": [
                {
                    "id": s.id,
                    "pair": s.pair,
                    "signal": s.signal,
                    "confidence": s.confidence,
                    "reason": s.reason,
                    "executed": s.executed,
                    "skip_reason": s.skip_reason,
                    "entry_price": s.entry_price,
                    "sl_price": s.sl_price,
                    "tp_price": s.tp_price,
                    "news_sentiment": s.news_sentiment,
                    "technical_score": s.technical_score,
                    "created_at": s.created_at.isoformat()
                }
                for s in signals
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
