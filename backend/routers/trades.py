"""
Trades router - Trade history endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.position import Position

router = APIRouter(prefix="/api/trades", tags=["trades"])


@router.get("")
async def get_trades(limit: int = 50, db: Session = Depends(get_db)):
    """Get trade history"""
    try:
        trades = db.query(Position).filter(
            Position.status == 'CLOSED'
        ).order_by(Position.closed_at.desc()).limit(limit).all()
        
        return {
            "success": True,
            "data": [
                {
                    "id": t.id,
                    "pair": t.pair,
                    "side": t.side,
                    "entry_price": float(t.entry_price),
                    "quantity": float(t.quantity),
                    "leverage": t.leverage,
                    "pnl": float(t.pnl) if t.pnl else 0,
                    "ai_reason": t.ai_reason,
                    "confidence": t.confidence,
                    "opened_at": t.opened_at.isoformat(),
                    "closed_at": t.closed_at.isoformat() if t.closed_at else None
                }
                for t in trades
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
