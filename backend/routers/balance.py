"""
Balance router - Account balance endpoints
"""
from fastapi import APIRouter, HTTPException
from modules.order_executor import OrderExecutor

router = APIRouter(prefix="/api/balance", tags=["balance"])

executor = OrderExecutor()


@router.get("")
async def get_balance():
    """Get account balance"""
    try:
        balance = executor.get_balance()
        return {
            "success": True,
            "data": balance
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
