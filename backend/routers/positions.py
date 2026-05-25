"""
Positions router - Trading positions endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.position import Position
from modules.position_manager import PositionManager
from typing import List

router = APIRouter(prefix="/api/positions", tags=["positions"])
position_manager = PositionManager()


@router.get("")
async def get_positions(db: Session = Depends(get_db)):
    """Get active trading positions"""
    try:
        positions = db.query(Position).filter(
            Position.status.in_(['OPEN', 'BE', 'TRAILING'])
        ).all()

        return {
            "success": True,
            "data": [
                {
                    "id": p.id,
                    "pair": p.pair,
                    "side": p.side,
                    "entry_price": float(p.entry_price),
                    "current_price": position_manager.get_current_price(p.pair),
                    "sl_price": float(p.sl_price),
                    "tp_price": float(p.tp_price),
                    "quantity": float(p.quantity),
                    "leverage": p.leverage,
                    "pnl": float(p.pnl or 0),
                    "status": p.status,
                    "ai_reason": p.ai_reason,
                    "opened_at": p.opened_at.isoformat(),
                    "closed_at": p.closed_at.isoformat() if p.closed_at else None,
                    "partial_closed": p.partial_closed
                }
                for p in positions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all")
async def get_all_positions(db: Session = Depends(get_db)):
    """Get all positions including closed"""
    try:
        positions = db.query(Position).order_by(Position.opened_at.desc()).limit(100).all()
        
        return {
            "success": True,
            "data": [
                {
                    "id": p.id,
                    "pair": p.pair,
                    "side": p.side,
                    "entry_price": float(p.entry_price),
                    "sl_price": float(p.sl_price),
                    "tp_price": float(p.tp_price),
                    "quantity": float(p.quantity),
                    "leverage": p.leverage,
                    "status": p.status,
                    "ai_reason": p.ai_reason,
                    "confidence": p.confidence,
                    "pnl": float(p.pnl) if p.pnl else 0,
                    "opened_at": p.opened_at.isoformat(),
                    "closed_at": p.closed_at.isoformat() if p.closed_at else None,
                    "partial_closed": p.partial_closed
                }
                for p in positions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
