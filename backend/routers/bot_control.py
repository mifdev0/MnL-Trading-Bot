"""
Bot Control router - Bot control endpoints
"""
from fastapi import APIRouter, HTTPException
from scheduler import pause_bot, resume_bot, is_bot_paused
from modules.order_executor import OrderExecutor

router = APIRouter(prefix="/api/bot", tags=["bot"])

executor = OrderExecutor()


@router.post("/pause")
async def pause():
    """Pause the bot"""
    try:
        pause_bot()
        return {
            "success": True,
            "message": "Bot paused"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resume")
async def resume():
    """Resume the bot"""
    try:
        resume_bot()
        return {
            "success": True,
            "message": "Bot resumed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """Get bot status"""
    try:
        paused = is_bot_paused()
        open_positions = executor.count_open_positions()
        balance = executor.get_balance()
        
        return {
            "success": True,
            "data": {
                "paused": paused,
                "status": "paused" if paused else "active",
                "open_positions": open_positions,
                "balance": balance
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
