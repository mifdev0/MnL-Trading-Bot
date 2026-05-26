"""
Telegram Bot - Interactive bot for monitoring and control
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import settings
from database import SessionLocal
from models.position import Position
from models.signal import Signal
from models.news import News
from modules.order_executor import OrderExecutor
from scheduler import pause_bot, resume_bot, is_bot_paused
from datetime import datetime, timedelta, timezone
from sqlalchemy import func

logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self):
        """Initialize Telegram Bot"""
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.executor = OrderExecutor()
        self.app = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
🤖 *MnL Trading Bot*

_AI that trades while you sleep._

*Available Commands:*
/balance - Check balance & margin
/positions - View active positions
/pnl - View profit/loss (Inc. Unrealized)
/news - Latest crypto news
/signals - Recent AI signals
/history - Trade history
/stats - Trading statistics
/status - Bot status
/scan - Trigger manual market scan
/pause - Pause bot
/resume - Resume bot
/closeall - Emergency close all positions
/help - Show this message

Use these commands to monitor and control your trading bot.
        """
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /balance command"""
        try:
            balance = self.executor.get_balance()
            
            message = f"""
💰 *Account Balance*

Total: ${balance['total']:.2f}
Available: ${balance['free']:.2f}
Used: ${balance['used']:.2f}
            """
            
            await update.message.reply_text(message, parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def positions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /positions command"""
        try:
            db = SessionLocal()
            positions = db.query(Position).filter(
                Position.status.in_(['OPEN', 'BE', 'TRAILING'])
            ).all()
            
            if not positions:
                await update.message.reply_text("📊 No active positions")
                return
            
            message = "📊 *Active Positions*\n\n"
            
            for pos in positions:
                # Get current price
                if self.executor.demo_mode:
                    current_price = self.executor.futures_client.get_price(pos.pair)
                else:
                    current_price = self.executor.exchange.fetch_ticker(pos.pair)['last']
                
                # Calculate PnL
                if pos.side == 'LONG':
                    pnl = (current_price - float(pos.entry_price)) * float(pos.quantity)
                else:
                    pnl = (float(pos.entry_price) - current_price) * float(pos.quantity)
                
                pnl_emoji = "🟢" if pnl > 0 else "🔴"
                
                message += f"""
*{pos.pair}* {pos.side}
Entry: ${float(pos.entry_price):.2f}
Current: ${current_price:.2f}
PnL: {pnl_emoji} ${pnl:.2f}
Status: {pos.status}
Reason: {pos.ai_reason[:50]}...

"""
            
            await update.message.reply_text(message, parse_mode='Markdown')
            db.close()
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def pnl_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /pnl command"""
        try:
            db = SessionLocal()
            
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
            
            today_total_pnl = float(closed_today_pnl) + float(unrealized_pnl)
            
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
            
            message = f"""
📈 *Profit & Loss*

Today (Inc. Unrel): ${today_total_pnl:.2f}
Unrealized: ${float(unrealized_pnl):.2f}
This Week: ${float(week_pnl):.2f}
This Month: ${float(month_pnl):.2f}
All Time: ${float(all_time_pnl):.2f}
            """
            
            await update.message.reply_text(message, parse_mode='Markdown')
            db.close()
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def news_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /news command"""
        try:
            db = SessionLocal()
            news_items = db.query(News).order_by(
                News.published_at.desc()
            ).limit(5).all()
            
            if not news_items:
                await update.message.reply_text("📰 No recent news")
                return
            
            message = "📰 *Latest Crypto News*\n\n"
            
            for news in news_items:
                sentiment_emoji = {
                    'bullish': '🟢',
                    'bearish': '🔴',
                    'neutral': '⚪'
                }.get(news.sentiment, '⚪')
                
                message += f"{sentiment_emoji} *{news.sentiment.upper()}*\n"
                message += f"{news.title}\n"
                message += f"_{news.source}_\n\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            db.close()
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def signals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /signals command"""
        try:
            db = SessionLocal()
            signals = db.query(Signal).order_by(
                Signal.created_at.desc()
            ).limit(5).all()
            
            if not signals:
                await update.message.reply_text("🎯 No recent signals")
                return
            
            message = "🎯 *Recent AI Signals*\n\n"
            
            for sig in signals:
                executed_emoji = "✅" if sig.executed else "⏭️"
                
                message += f"{executed_emoji} *{sig.pair}* {sig.signal}\n"
                message += f"Confidence: {sig.confidence}%\n"
                message += f"Reason: {sig.reason[:50]}...\n\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            db.close()
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /history command"""
        try:
            db = SessionLocal()
            positions = db.query(Position).filter(
                Position.status == 'CLOSED'
            ).order_by(Position.closed_at.desc()).limit(10).all()
            
            if not positions:
                await update.message.reply_text("📜 No trade history")
                return
            
            message = "📜 *Trade History (Last 10)*\n\n"
            
            for pos in positions:
                pnl_emoji = "🟢" if float(pos.pnl) > 0 else "🔴"
                
                # Format time to local
                closed_time = pos.closed_at
                if closed_time and closed_time.tzinfo is None:
                    # If naive, assume UTC
                    closed_time = closed_time.replace(tzinfo=timezone.utc)
                
                # Convert to local time if possible, otherwise just format
                time_str = closed_time.astimezone().strftime('%Y-%m-%d %H:%M') if closed_time else "N/A"
                
                message += f"{pnl_emoji} *{pos.pair}* {pos.side}\n"
                message += f"Entry: ${float(pos.entry_price):.2f}\n"
                message += f"PnL: ${float(pos.pnl):.2f}\n"
                message += f"Closed: {time_str}\n\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            db.close()
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        try:
            db = SessionLocal()
            
            # Total trades
            total_trades = db.query(Position).filter(Position.status == 'CLOSED').count()
            
            # Win rate
            winning_trades = db.query(Position).filter(
                Position.status == 'CLOSED',
                Position.pnl > 0
            ).count()
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Best trade
            best_trade = db.query(Position).filter(
                Position.status == 'CLOSED'
            ).order_by(Position.pnl.desc()).first()
            
            # Worst trade
            worst_trade = db.query(Position).filter(
                Position.status == 'CLOSED'
            ).order_by(Position.pnl.asc()).first()
            
            best_trade_str = f"${float(best_trade.pnl):.2f} ({best_trade.pair})" if best_trade else "N/A"
            worst_trade_str = f"${float(worst_trade.pnl):.2f} ({worst_trade.pair})" if worst_trade else "N/A"

            message = f"""
📊 *Trading Statistics*

Total Trades: {total_trades}
Winning Trades: {winning_trades}
Losing Trades: {total_trades - winning_trades}
Win Rate: {win_rate:.1f}%

Best Trade: {best_trade_str}
Worst Trade: {worst_trade_str}
            """
            
            await update.message.reply_text(message, parse_mode='Markdown')
            db.close()
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        try:
            paused = is_bot_paused()
            open_positions = self.executor.count_open_positions()
            balance = self.executor.get_balance()
            
            status_text = "⏸️ Paused" if paused else "✅ Active"
            
            message = f"""
🤖 *Bot Status*

Status: {status_text}
Open Positions: {open_positions}/{settings.MAX_OPEN_POSITIONS}
Available Balance: ${balance['free']:.2f}
Risk per Trade: {settings.RISK_PER_TRADE}%
Leverage: {settings.LEVERAGE}x
            """
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def scan_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /scan command"""
        try:
            await update.message.reply_text("🔍 Starting manual market scan and analysis... Please wait.")
            from scheduler import scan_and_analyze
            # Run in a separate thread to avoid blocking the bot
            import threading
            threading.Thread(target=scan_and_analyze, daemon=True).start()
            await update.message.reply_text("✅ Scan triggered. You will receive notifications if signals are found.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def pause_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /pause command"""
        try:
            pause_bot()
            await update.message.reply_text("⏸️ Bot paused successfully")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def resume_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /resume command"""
        try:
            resume_bot()
            await update.message.reply_text("✅ Bot resumed successfully")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def closeall_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /closeall command"""
        try:
            await update.message.reply_text("⚠️ Closing all positions... Please wait.")
            closed_count = self.executor.close_all_positions()
            await update.message.reply_text(f"✅ Successfully closed {closed_count} positions.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await self.start_command(update, context)
    
    async def send_notification(self, message: str):
        """
        Send notification to user
        
        Args:
            message: Message to send
        """
        try:
            if self.app:
                await self.app.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    async def run_async(self):
        """Run the bot asynchronously"""
        try:
            # Create application
            self.app = Application.builder().token(self.token).build()
            
            # Add command handlers
            self.app.add_handler(CommandHandler("start", self.start_command))
            self.app.add_handler(CommandHandler("balance", self.balance_command))
            self.app.add_handler(CommandHandler("positions", self.positions_command))
            self.app.add_handler(CommandHandler("pnl", self.pnl_command))
            self.app.add_handler(CommandHandler("news", self.news_command))
            self.app.add_handler(CommandHandler("signals", self.signals_command))
            self.app.add_handler(CommandHandler("history", self.history_command))
            self.app.add_handler(CommandHandler("stats", self.stats_command))
            self.app.add_handler(CommandHandler("status", self.status_command))
            self.app.add_handler(CommandHandler("scan", self.scan_command))
            self.app.add_handler(CommandHandler("pause", self.pause_command))
            self.app.add_handler(CommandHandler("resume", self.resume_command))
            self.app.add_handler(CommandHandler("closeall", self.closeall_command))
            self.app.add_handler(CommandHandler("help", self.help_command))
            
            logger.info("Telegram bot initialized (async mode)")
            
            # Start polling
            async with self.app:
                await self.app.initialize()
                await self.app.start()
                await self.app.updater.start_polling()
                logger.info("Telegram bot polling started")
                # Keep running until cancelled
                while True:
                    await asyncio.sleep(3600)
                    
        except Exception as e:
            logger.error(f"Error running Telegram bot (async): {e}")

    def run(self):
        """Run the bot (synchronous wrapper)"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.run_async())
        except Exception as e:
            logger.error(f"Error running Telegram bot: {e}")

    
# Global bot instance for notifications
bot_instance = None

def get_bot():
    """Get global bot instance"""
    global bot_instance
    if bot_instance is None:
        bot_instance = TelegramBot()
    return bot_instance


def notify(message: str):
    """
    Send notification via global bot instance (safe to call from any thread)
    """
    import asyncio
    
    bot = get_bot()
    if bot and bot.app:
        try:
            # Try to get the running loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(bot.send_notification(message))
            else:
                loop.run_until_complete(bot.send_notification(message))
        except Exception as e:
            # If no loop or other error, just log it
            logger.error(f"Failed to send notification: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bot = TelegramBot()
    bot.run()
