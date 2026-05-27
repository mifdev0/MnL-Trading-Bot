"""
Scheduler - Schedule periodic tasks
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from modules.scanner import MarketScanner
from modules.news_engine import NewsEngine
from modules.ai_signal import AISignalEngine
from modules.order_executor import OrderExecutor
from modules.position_manager import PositionManager
from database import SessionLocal
from models.signal import Signal
from models.position import Position

logger = logging.getLogger(__name__)

# Global instances
scanner = MarketScanner()
news_engine = NewsEngine()
ai_engine = AISignalEngine()
executor = OrderExecutor()
position_manager = PositionManager()

# Bot state
bot_paused = False


def scan_and_analyze():
    """
    Main trading loop: scan market → analyze → execute
    """
    global bot_paused
    
    if bot_paused:
        logger.info("Bot is paused, skipping scan")
        return
    
    try:
        logger.info("=" * 50)
        logger.info("Starting trading cycle...")
        
        # 1. Scan market for candidates
        logger.info("Step 1: Scanning market...")
        candidate_pairs = scanner.get_candidate_pairs()
        
        if not candidate_pairs:
            logger.warning("No candidate pairs found")
            return
        
        logger.info(f"Found {len(candidate_pairs)} candidate pairs")
        
        # 2. Analyze pairs with AI
        logger.info("Step 2: Analyzing with AI...")
        signals = ai_engine.analyze_multiple_pairs(candidate_pairs)
        
        if not signals:
            logger.warning("No signals generated")
            return
        
        # 3. Save signals to database
        db = SessionLocal()
        try:
            for signal in signals:
                signal_record = Signal(
                    pair=signal['pair'],
                    signal=signal['signal'],
                    confidence=signal['confidence'],
                    reason=signal['reason'],
                    executed=False,
                    skip_reason=signal.get('skip_reason'),
                    entry_price=str(signal.get('entry_price', 0)),
                    sl_price=str(signal.get('sl_price', 0)),
                    tp_price=str(signal.get('tp_price', 0)),
                    news_sentiment=signal.get('news_sentiment'),
                    technical_score=signal.get('technical_score')
                )
                db.add(signal_record)
            db.commit()
        except Exception as e:
            logger.error(f"Error saving signals: {e}")
            db.rollback()
        finally:
            db.close()
        
        # 4. Execute valid signals
        logger.info("Step 3: Executing signals...")
        for signal in signals:
            if signal['signal'] in ['LONG', 'SHORT'] and signal['confidence'] >= 65:
                # Check if position already exists for this pair to prevent duplicates
                db = SessionLocal()
                try:
                    existing = db.query(Position).filter(
                        Position.pair == signal['pair'],
                        Position.status.in_(['OPEN', 'BE', 'TRAILING'])
                    ).first()
                    if existing:
                        logger.info(f"Skipping {signal['pair']}: Already have an open position")
                        continue
                finally:
                    db.close()

                position = executor.execute_signal(signal)
                if position:
                    logger.info(f"✅ Position opened: {position.pair} {position.side}")
        
        logger.info("Trading cycle completed")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"Error in trading cycle: {e}")


def fetch_news():
    """
    Fetch news from all sources
    """
    try:
        logger.info("Fetching news...")
        news_engine.fetch_and_save_all_news()
    except Exception as e:
        logger.error(f"Error fetching news: {e}")


def manage_positions():
    """
    Manage all active positions
    """
    try:
        logger.debug("Managing positions...")
        position_manager.manage_all_positions()
    except Exception as e:
        logger.error(f"Error managing positions: {e}")


def pause_bot():
    """Pause the bot"""
    global bot_paused
    bot_paused = True
    logger.info("🛑 Bot paused")


def resume_bot():
    """Resume the bot"""
    global bot_paused
    bot_paused = False
    logger.info("▶️ Bot resumed")


def is_bot_paused():
    """Check if bot is paused"""
    return bot_paused


def heartbeat():
    """Simple heartbeat log to confirm scheduler is alive"""
    logger.info("💓 Scheduler heartbeat: Bot is active and monitoring...")


# Create scheduler
scheduler = BackgroundScheduler()


def start_scheduler():
    """
    Start the scheduler with all jobs
    """
    try:
        # Heartbeat every 1 minute
        scheduler.add_job(
            heartbeat,
            trigger=IntervalTrigger(minutes=1),
            id='heartbeat',
            name='Scheduler heartbeat',
            replace_existing=True
        )

        # Fetch news every 5 minutes
        scheduler.add_job(
            fetch_news,
            trigger=IntervalTrigger(minutes=5),
            id='fetch_news',
            name='Fetch crypto news',
            replace_existing=True
        )
        
        # Scan and analyze every 15 minutes
        scheduler.add_job(
            scan_and_analyze,
            trigger=IntervalTrigger(minutes=15),
            id='scan_and_analyze',
            name='Scan market and analyze',
            replace_existing=True
        )
        
        # Manage positions every 10 seconds
        scheduler.add_job(
            manage_positions,
            trigger=IntervalTrigger(seconds=10),
            id='manage_positions',
            name='Manage active positions',
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("✅ Scheduler started")
        
        # Run initial jobs in separate background threads to avoid blocking each other
        import threading
        
        logger.info("Running initial jobs in background...")
        threading.Thread(target=fetch_news, daemon=True).start()
        # Delay analysis by 5 seconds to ensure news/db is ready
        threading.Timer(5.0, scan_and_analyze).start()
        
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")


def stop_scheduler():
    """
    Stop the scheduler
    """
    try:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
