"""
Performance router - Performance metrics endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.position import Position
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/performance", tags=["performance"])


@router.get("")
async def get_performance(db: Session = Depends(get_db)):
    """Get performance metrics"""
    try:
        # Unrealized PnL from open positions
        unrealized_pnl = db.query(func.sum(Position.pnl)).filter(
            Position.status.in_(['OPEN', 'BE', 'TRAILING'])
        ).scalar() or 0

        # Today's PnL (Closed + Unrealized)
        today = datetime.now().date()
        closed_today_pnl = db.query(func.sum(Position.pnl)).filter(
            Position.closed_at >= today,
            Position.status == 'CLOSED'
        ).scalar() or 0
        
        today_pnl = float(closed_today_pnl) + float(unrealized_pnl)

        # This week's PnL
        week_ago = datetime.now() - timedelta(days=7)
        week_pnl = db.query(func.sum(Position.pnl)).filter(
            Position.closed_at >= week_ago,
            Position.status == 'CLOSED'
        ).scalar() or 0
        
        # This month's PnL
        month_ago = datetime.now() - timedelta(days=30)
        month_pnl = db.query(func.sum(Position.pnl)).filter(
            Position.closed_at >= month_ago,
            Position.status == 'CLOSED'
        ).scalar() or 0
        
        # All-time PnL
        all_time_pnl = db.query(func.sum(Position.pnl)).filter(
            Position.status == 'CLOSED'
        ).scalar() or 0
        
        # Total trades
        total_trades = db.query(Position).filter(Position.status == 'CLOSED').count()
        
        # Win rate
        winning_trades = db.query(Position).filter(
            Position.status == 'CLOSED',
            Position.pnl > 0
        ).count()
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Open positions
        open_positions = db.query(Position).filter(
            Position.status.in_(['OPEN', 'BE', 'TRAILING'])
        ).count()
        
        return {
            "success": True,
            "data": {
                "today_pnl": today_pnl,
                "unrealized_pnl": float(unrealized_pnl),
                "week_pnl": float(week_pnl),
                "month_pnl": float(month_pnl),
                "all_time_pnl": float(all_time_pnl),
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": total_trades - winning_trades,
                "win_rate": round(win_rate, 2),
                "open_positions": open_positions
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_performance_history(db: Session = Depends(get_db)):
    """Get aggregated performance history (daily and monthly)"""
    try:
        # Unrealized PnL from open positions to add to today's bar
        unrealized_pnl = db.query(func.sum(Position.pnl)).filter(
            Position.status.in_(['OPEN', 'BE', 'TRAILING'])
        ).scalar() or 0

        # 1. Daily History (Last 30 days)
        daily_cutoff = datetime.now() - timedelta(days=30)
        daily_trades = db.query(
            func.date(Position.closed_at).label('date'),
            func.sum(Position.pnl).label('pnl'),
            func.count(Position.id).label('trades')
        ).filter(
            Position.status == 'CLOSED',
            Position.closed_at >= daily_cutoff
        ).group_by(func.date(Position.closed_at)).order_by(func.date(Position.closed_at)).all()

        daily_history = [
            {
                "date": str(d.date),
                "pnl": float(d.pnl),
                "trades": d.trades
            }
            for d in daily_trades
        ]

        # Add current day if not present or update it with unrealized
        today_str = str(datetime.now().date())
        today_item = next((item for item in daily_history if item["date"] == today_str), None)
        
        if today_item:
            today_item["pnl"] += float(unrealized_pnl)
        else:
            daily_history.append({
                "date": today_str,
                "pnl": float(unrealized_pnl),
                "trades": 0
            })
        
        # Sort again just in case
        daily_history.sort(key=lambda x: x["date"])

        # 2. Monthly History (Last 12 months)
        monthly_cutoff = datetime.now() - timedelta(days=365)
        
        # Determine DB type for grouping
        is_sqlite = db.bind.dialect.name == 'sqlite'
        
        if is_sqlite:
            month_label = func.strftime('%Y-%m', Position.closed_at)
        else:
            month_label = func.to_char(Position.closed_at, 'YYYY-MM')

        monthly_trades = db.query(
            month_label.label('month'),
            func.sum(Position.pnl).label('pnl'),
            func.count(Position.id).label('trades')
        ).filter(
            Position.status == 'CLOSED',
            Position.closed_at >= monthly_cutoff
        ).group_by('month').order_by('month').all()

        monthly_history = [
            {
                "month": m.month,
                "pnl": float(m.pnl),
                "trades": m.trades
            }
            for m in monthly_trades
        ]

        # Add unrealized to current month
        current_month = datetime.now().strftime('%Y-%m')
        month_item = next((item for item in monthly_history if item["month"] == current_month), None)
        if month_item:
            month_item["pnl"] += float(unrealized_pnl)
        elif unrealized_pnl != 0:
            monthly_history.append({
                "month": current_month,
                "pnl": float(unrealized_pnl),
                "trades": 0
            })

        return {
            "success": True,
            "data": {
                "daily": daily_history,
                "monthly": monthly_history
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/equity")
async def get_equity_curve(days: int = 30, db: Session = Depends(get_db)):
    """Get equity curve data"""
    try:
        cutoff = datetime.now() - timedelta(days=days)
        
        trades = db.query(Position).filter(
            Position.status == 'CLOSED',
            Position.closed_at >= cutoff
        ).order_by(Position.closed_at.asc()).all()
        
        equity_data = []
        cumulative_pnl = 0
        
        for trade in trades:
            cumulative_pnl += float(trade.pnl) if trade.pnl else 0
            equity_data.append({
                "date": trade.closed_at.isoformat(),
                "pnl": float(trade.pnl) if trade.pnl else 0,
                "cumulative_pnl": cumulative_pnl
            })
        
        return {
            "success": True,
            "data": equity_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
