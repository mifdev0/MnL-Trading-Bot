"""
Manual Trigger Router - Manually trigger trading cycle for testing
"""
from fastapi import APIRouter, HTTPException
from scheduler import scan_and_analyze, fetch_news, manage_positions
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/manual", tags=["manual"])


@router.post("/scan")
async def trigger_scan():
    """
    Manually trigger market scan and AI analysis
    """
    try:
        logger.info("Manual scan triggered via API")
        scan_and_analyze()
        return {
            "status": "success",
            "message": "Market scan and analysis triggered. Check logs for results."
        }
    except Exception as e:
        logger.error(f"Error in manual scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/news")
async def trigger_news():
    """
    Manually trigger news fetch
    """
    try:
        logger.info("Manual news fetch triggered via API")
        fetch_news()
        return {
            "status": "success",
            "message": "News fetch triggered. Check logs for results."
        }
    except Exception as e:
        logger.error(f"Error in manual news fetch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/positions")
async def trigger_position_management():
    """
    Manually trigger position management
    """
    try:
        logger.info("Manual position management triggered via API")
        manage_positions()
        return {
            "status": "success",
            "message": "Position management triggered. Check logs for results."
        }
    except Exception as e:
        logger.error(f"Error in manual position management: {e}")
        raise HTTPException(status_code=500, detail=str(e))
