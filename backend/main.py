"""
Main FastAPI application
"""
import logging
import asyncio
import threading
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import settings
from database import init_db
from scheduler import start_scheduler, stop_scheduler
from routers import balance, positions, trades, performance, news, signals, bot_control
import json
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logging.getLogger("apscheduler.executors.default").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# WebSocket connections
active_connections: List[WebSocket] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting MnL Trading Bot System...")
    
    # Initialize database
    logger.info("Initializing database...")
    init_db()
    
    # Start scheduler
    logger.info("Starting scheduler...")
    start_scheduler()
    
    # Start Telegram bot in a separate thread
    logger.info("Starting Telegram bot...")
    from modules.telegram_bot import TelegramBot
    bot = TelegramBot()
    bot_thread = threading.Thread(target=bot.run, daemon=True)
    bot_thread.start()
    
    logger.info("[OK] System started successfully")
    logger.info(f"API running on port {settings.API_PORT}")
    logger.info(f"Telegram bot running")
    logger.info(f"Binance demo mode: {settings.BINANCE_TESTNET}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    stop_scheduler()
    logger.info("System stopped")


# Create FastAPI app
app = FastAPI(
    title="MnL Trading Bot API",
    description="AI-powered crypto trading bot with realtime monitoring",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(balance.router)
app.include_router(positions.router)
app.include_router(trades.router)
app.include_router(performance.router)
app.include_router(news.router)
app.include_router(signals.router)
app.include_router(bot_control.router)

# Import manual trigger router
from routers import manual_trigger
app.include_router(manual_trigger.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "MnL Trading Bot API",
        "version": "1.0.0",
        "status": "running",
        "demo_mode": settings.BINANCE_TESTNET
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time()
    }


@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for realtime updates
    """
    await websocket.accept()
    active_connections.append(websocket)
    logger.info(f"WebSocket client connected. Total: {len(active_connections)}")
    
    try:
        while True:
            # Keep connection alive and send updates
            # In a real implementation, you would send actual updates here
            await asyncio.sleep(5)
            
            # Send heartbeat
            await websocket.send_json({
                "type": "heartbeat",
                "timestamp": asyncio.get_event_loop().time()
            })
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(active_connections)}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)


async def broadcast_update(data: dict):
    """
    Broadcast update to all connected WebSocket clients
    
    Args:
        data: Data to broadcast
    """
    for connection in active_connections:
        try:
            await connection.send_json(data)
        except Exception as e:
            logger.error(f"Error broadcasting to client: {e}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.API_PORT,
        reload=False,
        log_level="info"
    )
