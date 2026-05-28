"""
Order Executor - Execute trading orders on Binance Futures
"""
import ccxt
import logging
from typing import Dict, Optional
from decimal import Decimal
from sqlalchemy.sql import func
from config import settings
from database import SessionLocal
from models.position import Position
from models.signal import Signal
from modules.binance_futures import BinanceFuturesClient

logger = logging.getLogger(__name__)


class OrderExecutor:
    def __init__(self):
        """Initialize Binance exchange connection"""
        self.demo_mode = settings.BINANCE_TESTNET
        self.simulated_balance = 20.0  # $20 starting balance for simulation
        self.futures_client = BinanceFuturesClient(self.demo_mode)

        self.exchange = ccxt.binance({
            'apiKey': settings.BINANCE_API_KEY,
            'secret': settings.BINANCE_SECRET_KEY,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',
            }
        })

        if self.demo_mode:
            logger.info("Order Executor initialized in DEMO mode")
        else:
            logger.warning("Order Executor initialized in LIVE mode - REAL MONEY!")

    def _is_simulated_order_id(self, order_id: str) -> bool:
        return bool(order_id and str(order_id).startswith("SIM"))

    def _is_simulated_position(self, position: Position) -> bool:
        return any(
            self._is_simulated_order_id(order_id)
            for order_id in (position.order_id, position.sl_order_id, position.tp_order_id)
        )

    def get_balance(self) -> Dict:
        """
        Get account balance
        
        Returns:
            Balance dictionary
        """
        try:
            if self.demo_mode:
                return self.futures_client.get_balance()

            balance = self.exchange.fetch_balance()
            return {
                'total': balance['USDT']['total'],
                'free': balance['USDT']['free'],
                'used': balance['USDT']['used']
            }
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            # Return simulated balance as fallback
            return {
                'total': self.simulated_balance,
                'free': self.simulated_balance,
                'used': 0
            }
    
    def count_open_positions(self) -> int:
        """
        Count currently open positions
        
        Returns:
            Number of open positions
        """
        db = SessionLocal()
        try:
            count = db.query(Position).filter(
                Position.status.in_(['OPEN', 'BE', 'TRAILING'])
            ).count()
            return count
        finally:
            db.close()
    
    def calculate_position_size(self, entry_price: float, sl_price: float, balance: float) -> float:
        """
        Calculate position size based on risk management
        
        Args:
            entry_price: Entry price
            sl_price: Stop loss price
            balance: Available balance
            
        Returns:
            Position size in base currency
        """
        # Risk amount in USDT
        capped_balance = min(balance, settings.MAX_BALANCE_CAP) if settings.MAX_BALANCE_CAP > 0 else balance
        risk_amount = capped_balance * (settings.RISK_PER_TRADE / 100)
        logger.info(f"Balance cap applied: ${capped_balance:.2f} (actual: ${balance:.2f}), risk: ${risk_amount:.2f}")
        
        # Risk per unit
        risk_per_unit = abs(entry_price - sl_price)
        
        # Position size
        position_size = risk_amount / risk_per_unit
        
        return position_size
    
    def set_leverage(self, symbol: str, leverage: int):
        """
        Set leverage for a symbol
        
        Args:
            symbol: Trading pair symbol
            leverage: Leverage value
        """
        try:
            if self.demo_mode:
                self.futures_client.set_leverage(symbol, leverage)
            else:
                self.exchange.set_leverage(leverage, symbol)
            logger.info(f"Set leverage {leverage}x for {symbol}")
        except Exception as e:
            logger.error(f"Error setting leverage for {symbol}: {e}")

    def _execute_demo_orders(self, symbol: str, side: str, quantity: float, sl_price: float, tp_price: float):
        self.set_leverage(symbol, settings.LEVERAGE)

        order = self.futures_client.create_market_order(symbol, side, quantity)
        logger.info(f"Demo market order executed: {order['id']}")

        close_side = 'sell' if side == 'buy' else 'buy'
        sl_order = self.futures_client.create_close_algo_order(
            symbol,
            close_side,
            'STOP_MARKET',
            sl_price,
        )
        logger.info(f"Demo stop loss placed: {sl_order['id']}")

        tp_order = self.futures_client.create_close_algo_order(
            symbol,
            close_side,
            'TAKE_PROFIT_MARKET',
            tp_price,
        )
        logger.info(f"Demo take profit placed: {tp_order['id']}")

        return order, sl_order, tp_order
    
    def execute_signal(self, signal: Dict) -> Optional[Position]:
        """
        Execute a trading signal
        
        Args:
            signal: Signal dictionary from AI engine
            
        Returns:
            Position object if successful, None otherwise
        """
        try:
            # Validate signal
            if signal['signal'] not in ['LONG', 'SHORT']:
                logger.info(f"Skipping {signal['pair']}: {signal.get('skip_reason', 'No signal')}")
                return None
            
            # Check max positions
            open_positions = self.count_open_positions()
            if open_positions >= settings.MAX_OPEN_POSITIONS:
                logger.warning(f"Max positions reached ({open_positions}/{settings.MAX_OPEN_POSITIONS})")
                return None
            
            # Get balance
            balance = self.get_balance()
            
            # Cap balance jika MAX_BALANCE_CAP di-set
            raw_free = balance['free']
            if settings.MAX_BALANCE_CAP > 0:
                capped = min(raw_free, settings.MAX_BALANCE_CAP)
            else:
                capped = raw_free

            # Log supaya keliatan
            logger.info(f"Balance cap: ${capped} (actual free: ${raw_free})")

            if raw_free < 10:  # tetap cek saldo asli, bukan capped
                logger.warning(f"Insufficient balance: ${raw_free}")
                return None
            
            symbol = signal['pair']
            side = 'buy' if signal['signal'] == 'LONG' else 'sell'
            entry_price = signal['entry_price']
            sl_price = signal['sl_price']
            tp_price = signal['tp_price']
            
            # Calculate position size menggunakan saldo yang di-cap
            quantity = self.calculate_position_size(entry_price, sl_price, capped)
            
            logger.info(f"{'[DEMO]' if self.demo_mode else '[LIVE]'} Executing {side.upper()} order for {symbol}")
            logger.info(f"Entry: ${entry_price}, SL: ${sl_price}, TP: ${tp_price}, Qty: {quantity}")

            if self.demo_mode:
                quantity = float(self.futures_client.format_quantity(symbol, quantity))
                order, sl_order, tp_order = self._execute_demo_orders(
                    symbol,
                    side,
                    quantity,
                    sl_price,
                    tp_price,
                )
            else:
                self.set_leverage(symbol, settings.LEVERAGE)
                
                # Round quantity to exchange precision
                self.exchange.load_markets()
                quantity = float(self.exchange.amount_to_precision(symbol, quantity))
                
                # Place market order
                order = self.exchange.create_order(
                    symbol=symbol,
                    type='market',
                    side=side,
                    amount=quantity
                )

                logger.info(f"Order executed: {order['id']}")

                # Place stop loss order
                sl_side = 'sell' if side == 'buy' else 'buy'
                sl_order = self.exchange.create_order(
                    symbol=symbol,
                    type='stop_market',
                    side=sl_side,
                    amount=quantity,
                    params={'stopPrice': sl_price}
                )

                logger.info(f"Stop loss placed: {sl_order['id']}")

                # Place take profit order
                tp_order = self.exchange.create_order(
                    symbol=symbol,
                    type='take_profit_market',
                    side=sl_side,
                    amount=quantity,
                    params={'stopPrice': tp_price}
                )

                logger.info(f"Take profit placed: {tp_order['id']}")

            order_id = order['id']
            sl_order_id = sl_order['id']
            tp_order_id = tp_order['id']
            
            # Save position to database
            db = SessionLocal()
            try:
                position = Position(
                    pair=symbol,
                    side=signal['signal'],
                    entry_price=Decimal(str(entry_price)),
                    sl_price=Decimal(str(sl_price)),
                    tp_price=Decimal(str(tp_price)),
                    quantity=Decimal(str(quantity)),
                    leverage=settings.LEVERAGE,
                    status='OPEN',
                    ai_reason=signal['reason'],
                    news_used=signal.get('news_sentiment', ''),
                    confidence=signal['confidence'],
                    order_id=order_id,
                    sl_order_id=sl_order_id,
                    tp_order_id=tp_order_id
                )
                
                db.add(position)
                db.commit()
                db.refresh(position)
                
                logger.info(f"Position saved to database: {position.id}")
                
                # Send notification
                from modules.telegram_bot import notify
                message = f"✅ *Position Opened*\n\n"
                message += f"Pair: `{position.pair}`\n"
                message += f"Side: *{position.side}*\n"
                message += f"Entry: `${float(position.entry_price):.2f}`\n"
                message += f"SL: `${float(position.sl_price):.2f}`\n"
                message += f"TP: `${float(position.tp_price):.2f}`\n"
                message += f"Confidence: {position.confidence}%\n\n"
                message += f"_Reason: {position.ai_reason[:100]}..._"
                notify(message)

                # Save signal as executed
                signal_record = Signal(
                    pair=symbol,
                    signal=signal['signal'],
                    confidence=signal['confidence'],
                    reason=signal['reason'],
                    executed=True,
                    entry_price=str(entry_price),
                    sl_price=str(sl_price),
                    tp_price=str(tp_price),
                    news_sentiment=signal.get('news_sentiment'),
                    technical_score=signal.get('technical_score')
                )
                db.add(signal_record)
                db.commit()

                db.refresh(position)
                db.expunge(position)
                
                return position
                
            except Exception as e:
                logger.error(f"Error saving position to database: {e}")
                db.rollback()
                return None
            finally:
                db.close()
            
        except Exception as e:
            logger.error(f"Error executing signal for {signal['pair']}: {e}")
            return None
    
    def close_position(self, position: Position, reason: str = "Manual close") -> bool:
        """
        Close a position manually
        
        Args:
            position: Position object
            reason: Reason for closing
            
        Returns:
            True if successful, False otherwise
        """
        try:
            symbol = position.pair
            side = 'sell' if position.side == 'LONG' else 'buy'
            quantity = float(position.quantity)
            
            # Close position
            if self._is_simulated_position(position):
                order = {'id': f"{position.order_id}_CLOSE", 'average': float(position.entry_price)}
                logger.info(f"[SIMULATION] Position closed: {order['id']} - {reason}")
            elif self.demo_mode:
                order = self.futures_client.create_market_order(symbol, side, quantity, reduce_only=True)
                order['average'] = self.futures_client.get_price(symbol)
            else:
                # Use self.exchange (CCXT) for live modes
                order = self.exchange.create_order(
                    symbol=symbol,
                    type='market',
                    side=side,
                    amount=quantity,
                    params={'reduceOnly': True}
                )
                
                # If order average is not returned, fetch current price as fallback
                if 'average' not in order or not order['average']:
                    try:
                        ticker = self.exchange.fetch_ticker(symbol)
                        order['average'] = ticker['last']
                    except:
                        order['average'] = float(position.entry_price) # Fallback to entry
            
            logger.info(f"Position closed: {order['id']} - {reason}")
            
            # Cancel SL and TP orders
            try:
                if position.sl_order_id and not self._is_simulated_order_id(position.sl_order_id):
                    if self.demo_mode:
                        self.futures_client.cancel_order(symbol, position.sl_order_id)
                    else:
                        self.exchange.cancel_order(position.sl_order_id, symbol)
                if position.tp_order_id and not self._is_simulated_order_id(position.tp_order_id):
                    if self.demo_mode:
                        self.futures_client.cancel_order(symbol, position.tp_order_id)
                    else:
                        self.exchange.cancel_order(position.tp_order_id, symbol)
            except Exception as e:
                logger.warning(f"Error canceling orders: {e}")
            
            # Update position in database
            db = SessionLocal()
            try:
                # Calculate PnL
                current_price = order['average']
                if position.side == 'LONG':
                    pnl = (current_price - float(position.entry_price)) * float(position.quantity)
                else:
                    pnl = (float(position.entry_price) - current_price) * float(position.quantity)

                db_position = db.query(Position).get(position.id)
                if db_position:
                    db_position.status = 'CLOSED'
                    from datetime import datetime, timezone
                    db_position.closed_at = datetime.now(timezone.utc)
                    db_position.pnl = Decimal(str(pnl))
                
                db.commit()
                logger.info(f"Position updated in database: PnL ${pnl:.2f}")
                
                # Send notification
                from modules.telegram_bot import notify
                pnl_emoji = "🟢" if pnl > 0 else "🔴"
                message = f"🏁 *Position Closed*\n\n"
                message += f"Pair: `{position.pair}`\n"
                message += f"Side: *{position.side}*\n"
                message += f"PnL: {pnl_emoji} *${pnl:.2f}*\n"
                message += f"Reason: {reason}"
                notify(message)

                return True
                
            except Exception as e:
                logger.error(f"Error updating position in database: {e}")
                db.rollback()
                return False
            finally:
                db.close()
            
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return False

    def close_all_positions(self) -> int:
        """
        Close all currently open positions
        
        Returns:
            Number of successfully closed positions
        """
        db = SessionLocal()
        try:
            positions = db.query(Position).filter(
                Position.status.in_(['OPEN', 'BE', 'TRAILING'])
            ).all()
            
            closed_count = 0
            for pos in positions:
                if self.close_position(pos, "Emergency close"):
                    closed_count += 1
            
            return closed_count
        finally:
            db.close()


if __name__ == "__main__":
    # Test order executor
    logging.basicConfig(level=logging.INFO)
    
    executor = OrderExecutor()
    balance = executor.get_balance()
    print(f"Balance: {balance}")
