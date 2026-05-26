"""
Position Manager - Manage active positions with BE, Partial TP, and Trailing Stop
"""
import ccxt
import logging
import requests
from typing import List
from decimal import Decimal
from datetime import datetime
from config import settings
from database import SessionLocal
from models.position import Position
from modules.binance_futures import BinanceFuturesClient

logger = logging.getLogger(__name__)


class PositionManager:
    def __init__(self):
        """Initialize Position Manager"""
        self.exchange = ccxt.binance({
            'apiKey': settings.BINANCE_API_KEY,
            'secret': settings.BINANCE_SECRET_KEY,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',
            }
        })
        self.market_exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',
            }
        })
        self.market_base_url = (
            'https://testnet.binancefuture.com'
            if settings.BINANCE_TESTNET
            else 'https://fapi.binance.com'
        )
        self.futures_client = BinanceFuturesClient(settings.BINANCE_TESTNET)
        self.price_error_logged_at = {}
        
        if settings.BINANCE_TESTNET:
            self.exchange.enable_demo_trading(True)
            logger.info("Position Manager initialized in DEMO mode")
        else:
            logger.info("Position Manager initialized in LIVE mode")

    def _is_simulated_order_id(self, order_id: str) -> bool:
        return bool(order_id and str(order_id).startswith("SIM"))

    def _has_simulated_orders(self, position: Position) -> bool:
        return any(
            self._is_simulated_order_id(order_id)
            for order_id in (position.order_id, position.sl_order_id, position.tp_order_id)
        )

    def _cancel_order_if_real(self, order_id: str, symbol: str):
        if self._is_simulated_order_id(order_id):
            logger.debug(f"Skipping simulated order cancel: {order_id}")
            return

        try:
            if settings.BINANCE_TESTNET:
                self.futures_client.cancel_order(symbol, order_id)
            else:
                self.exchange.cancel_order(order_id, symbol)
        except Exception as e:
            # If order is already canceled or not found, it's fine
            error_msg = str(e).lower()
            if "not found" in error_msg or "-2011" in error_msg or "already canceled" in error_msg:
                logger.debug(f"Order {order_id} already canceled or not found on exchange")
            else:
                raise e

    def _create_managed_order(self, position: Position, order_kind: str, **kwargs) -> dict:
        if self._has_simulated_orders(position):
            import time
            order_id = f"SIM_{order_kind}_{int(time.time() * 1000)}"
            logger.info(f"[SIMULATION] {order_kind} updated for {position.pair}: {order_id}")
            return {'id': order_id}

        if settings.BINANCE_TESTNET:
            order_type = str(kwargs.get('type', '')).upper()
            side = kwargs.get('side')
            if order_type == 'STOP_MARKET':
                stop_price = kwargs.get('params', {}).get('stopPrice')
                return self.futures_client.create_close_algo_order(
                    position.pair,
                    side,
                    'STOP_MARKET',
                    stop_price,
                )
            if order_type == 'MARKET':
                return self.futures_client.create_market_order(
                    position.pair,
                    side,
                    kwargs.get('amount'),
                    reduce_only=True,
                )

        return self.exchange.create_order(**kwargs)

    def _log_price_error(self, symbol: str, error: Exception):
        now = datetime.now().timestamp()
        last_logged_at = self.price_error_logged_at.get(symbol, 0)
        if now - last_logged_at >= 300:
            logger.error(f"Error fetching price for {symbol}: {error}")
            self.price_error_logged_at[symbol] = now

    def is_position_open_on_exchange(self, position: Position) -> bool:
        if self._has_simulated_orders(position):
            return True

        if not settings.BINANCE_TESTNET:
            return True

        exchange_position = self.futures_client.get_position(position.pair)
        if exchange_position:
            return abs(float(exchange_position.get('positionAmt', 0))) > 0

        return False

    def close_local_position(self, position: Position, reason: str):
        db = SessionLocal()
        try:
            db_position = db.query(Position).get(position.id)
            if db_position and db_position.status in ['OPEN', 'BE', 'TRAILING']:
                db_position.status = 'CLOSED'
                db_position.closed_at = datetime.now()
                db.commit()
                logger.info(f"Position {position.pair} marked CLOSED locally: {reason}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error closing local position {position.pair}: {e}")
        finally:
            db.close()
    
    def get_active_positions(self) -> List[Position]:
        """
        Get all active positions from database
        
        Returns:
            List of active Position objects
        """
        db = SessionLocal()
        try:
            positions = db.query(Position).filter(
                Position.status.in_(['OPEN', 'BE', 'TRAILING'])
            ).all()
            return positions
        finally:
            db.close()
    
    def get_current_price(self, symbol: str) -> float:
        """
        Get current market price for a symbol
        """
        try:
            if settings.BINANCE_TESTNET:
                return self.futures_client.get_price(symbol)

            market_symbol = symbol.split(':')[0].replace('/', '')
            response = requests.get(
                f'{self.market_base_url}/fapi/v1/ticker/price',
                params={'symbol': market_symbol},
                timeout=10,
                verify=True
            )
            response.raise_for_status()
            return float(response.json()['price'])
        except Exception as e:
            self._log_price_error(symbol, e)
            try:
                # Fallback to fetch_ohlcv if fetch_ticker fails
                ohlcv = self.market_exchange.fetch_ohlcv(symbol, timeframe='1m', limit=1)
                if ohlcv:
                    return float(ohlcv[0][4]) # Close price
            except:
                pass
            return 0
    
    def calculate_r_multiple(self, position: Position, current_price: float) -> float:
        """
        Calculate R-multiple (risk-reward ratio) for a position
        
        Args:
            position: Position object
            current_price: Current market price
            
        Returns:
            R-multiple value
        """
        entry = float(position.entry_price)
        sl = float(position.sl_price)
        
        # Risk per unit (R)
        risk = abs(entry - sl)
        
        if risk == 0:
            return 0
        
        # Profit/loss per unit
        if position.side == 'LONG':
            pnl_per_unit = current_price - entry
        else:  # SHORT
            pnl_per_unit = entry - current_price
        
        # R-multiple
        r_multiple = pnl_per_unit / risk
        
        return r_multiple
    
    def move_to_break_even(self, position: Position, current_price: float) -> bool:
        """
        Move stop loss to break even
        
        Args:
            position: Position object
            current_price: Current market price
            
        Returns:
            True if successful, False otherwise
        """
        try:
            entry = float(position.entry_price)
            
            # Calculate BE price with buffer
            if position.side == 'LONG':
                be_price = entry * (1 + settings.BE_BUFFER_PCT / 100)
            else:  # SHORT
                be_price = entry * (1 - settings.BE_BUFFER_PCT / 100)
            
            # Cancel old SL order
            if position.sl_order_id:
                try:
                    self._cancel_order_if_real(position.sl_order_id, position.pair)
                except Exception as e:
                    logger.warning(f"Error canceling old SL: {e}")
            
            # Place new SL at BE
            side = 'sell' if position.side == 'LONG' else 'buy'
            sl_order = self._create_managed_order(
                position,
                'BE_SL',
                symbol=position.pair,
                type='stop_market',
                side=side,
                amount=float(position.quantity),
                params={'stopPrice': be_price}
            )
            
            # Update position in database
            db = SessionLocal()
            try:
                db_position = db.query(Position).get(position.id)
                if db_position:
                    db_position.status = 'BE'
                    db_position.sl_price = Decimal(str(be_price))
                    db_position.sl_order_id = sl_order['id']
                    db.commit()
                
                logger.info(f"✅ Break Even activated for {position.pair} at ${be_price:.2f}")
                
                # Notification
                from modules.telegram_bot import notify
                notify(f"🛡️ *Break Even Activated*\nPair: `{position.pair}`\nNew SL: `${be_price:.2f}`")
                
                return True
                
            except Exception as e:
                logger.error(f"Error updating position to BE: {e}")
                db.rollback()
                return False
            finally:
                db.close()
            
        except Exception as e:
            logger.error(f"Error moving to break even: {e}")
            return False
    
    def execute_partial_tp(self, position: Position, current_price: float) -> bool:
        """
        Execute partial take profit (close 50% of position)
        
        Args:
            position: Position object
            current_price: Current market price
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Close 50% of position
            side = 'sell' if position.side == 'LONG' else 'buy'
            partial_quantity = float(position.quantity) * 0.5
            
            order = self._create_managed_order(
                position,
                'PARTIAL_TP',
                symbol=position.pair,
                type='market',
                side=side,
                amount=partial_quantity
            )
            
            logger.info(f"💰 Partial TP executed for {position.pair}: {partial_quantity} units")
            
            # Update position in database
            db = SessionLocal()
            try:
                # Calculate partial PnL
                if position.side == 'LONG':
                    partial_pnl = (current_price - float(position.entry_price)) * partial_quantity
                else:
                    partial_pnl = (float(position.entry_price) - current_price) * partial_quantity

                db_position = db.query(Position).get(position.id)
                if db_position:
                    db_position.partial_closed = True
                    db_position.quantity = Decimal(str(float(position.quantity) * 0.5))
                    db_position.pnl = Decimal(str(partial_pnl))
                    db.commit()
                
                logger.info(f"Partial PnL: ${partial_pnl:.2f}")
                
                # Notification
                from modules.telegram_bot import notify
                notify(f"💰 *Partial TP Executed*\nPair: `{position.pair}`\nPnL: *${partial_pnl:.2f}*")
                
                return True
                
            except Exception as e:
                logger.error(f"Error updating position after partial TP: {e}")
                db.rollback()
                return False
            finally:
                db.close()
            
        except Exception as e:
            logger.error(f"Error executing partial TP: {e}")
            return False
    
    def update_trailing_stop(self, position: Position, current_price: float) -> bool:
        """
        Update trailing stop loss
        
        Args:
            position: Position object
            current_price: Current market price
            
        Returns:
            True if updated, False otherwise
        """
        try:
            entry = float(position.entry_price)
            sl = float(position.sl_price)
            risk = abs(entry - sl)
            
            # Calculate trailing distance
            trailing_distance = risk * settings.TRAILING_DISTANCE_R
            
            # Update highest/lowest price
            db = SessionLocal()
            try:
                if position.side == 'LONG':
                    # Update highest price
                    if position.highest_price is None or current_price > float(position.highest_price):
                        db_position = db.query(Position).get(position.id)
                        if db_position:
                            db_position.highest_price = Decimal(str(current_price))
                        
                        # Calculate new trailing SL
                        new_sl = current_price - trailing_distance
                        
                        # Only update if new SL is higher than current SL
                        if new_sl > float(position.sl_price):
                            # Cancel old SL
                            if position.sl_order_id:
                                try:
                                    self._cancel_order_if_real(position.sl_order_id, position.pair)
                                except:
                                    pass
                            
                            # Place new trailing SL
                            sl_order = self._create_managed_order(
                                position,
                                'TRAILING_SL',
                                symbol=position.pair,
                                type='stop_market',
                                side='sell',
                                amount=float(position.quantity),
                                params={'stopPrice': new_sl}
                            )
                            
                            if db_position:
                                db_position.sl_price = Decimal(str(new_sl))
                                db_position.sl_order_id = sl_order['id']
                                db_position.status = 'TRAILING'
                            
                            db.commit()
                            logger.info(f"🎯 Trailing SL updated for {position.pair}: ${new_sl:.2f}")
                            
                            # Notification
                            from modules.telegram_bot import notify
                            notify(f"🎯 *Trailing SL Updated*\nPair: `{position.pair}`\nNew SL: `${new_sl:.2f}`")
                            
                            return True
                
                else:  # SHORT
                    # Update lowest price
                    if position.lowest_price is None or current_price < float(position.lowest_price):
                        db_position = db.query(Position).get(position.id)
                        if db_position:
                            db_position.lowest_price = Decimal(str(current_price))
                        
                        # Calculate new trailing SL
                        new_sl = current_price + trailing_distance
                        
                        # Only update if new SL is lower than current SL
                        if new_sl < float(position.sl_price):
                            # Cancel old SL
                            if position.sl_order_id:
                                try:
                                    self._cancel_order_if_real(position.sl_order_id, position.pair)
                                except:
                                    pass
                            
                            # Place new trailing SL
                            sl_order = self._create_managed_order(
                                position,
                                'TRAILING_SL',
                                symbol=position.pair,
                                type='stop_market',
                                side='buy',
                                amount=float(position.quantity),
                                params={'stopPrice': new_sl}
                            )
                            
                            if db_position:
                                db_position.sl_price = Decimal(str(new_sl))
                                db_position.sl_order_id = sl_order['id']
                                db_position.status = 'TRAILING'
                            
                            db.commit()
                            logger.info(f"🎯 Trailing SL updated for {position.pair}: ${new_sl:.2f}")
                            
                            # Notification
                            from modules.telegram_bot import notify
                            notify(f"🎯 *Trailing SL Updated*\nPair: `{position.pair}`\nNew SL: `${new_sl:.2f}`")
                            
                            return True
                
                db.commit()
                return False
                
            except Exception as e:
                logger.error(f"Error updating trailing stop: {e}")
                db.rollback()
                return False
            finally:
                db.close()
            
        except Exception as e:
            logger.error(f"Error in trailing stop logic: {e}")
            return False
    
    def manage_position(self, position: Position):
        """
        Manage a single position - update PnL and check for BE, Partial TP, and Trailing Stop
        """
        try:
            try:
                if not self.is_position_open_on_exchange(position):
                    self.close_local_position(position, "closed manually on exchange")
                    return
            except Exception as e:
                logger.warning(f"Could not sync exchange position for {position.pair}: {e}")

            # Get current price
            current_price = self.get_current_price(position.pair)
            if current_price == 0:
                return
            
            # Update PnL in database for real-time tracking
            db = SessionLocal()
            try:
                # Calculate current PnL
                entry = float(position.entry_price)
                qty = float(position.quantity)
                
                if position.side == 'LONG':
                    pnl = (current_price - entry) * qty
                else:
                    pnl = (entry - current_price) * qty
                
                # Update PnL in the database session
                db_position = db.query(Position).get(position.id)
                if db_position:
                    db_position.pnl = Decimal(str(pnl))
                    db.commit()
            except Exception as e:
                logger.error(f"Error updating live PnL: {e}")
                db.rollback()
            finally:
                db.close()

            # Calculate R-multiple
            r_multiple = self.calculate_r_multiple(position, current_price)
            
            logger.debug(f"{position.pair}: R={r_multiple:.2f}, Status={position.status}, Price=${current_price:.2f}")
            
            # Check for Break Even
            if position.status == 'OPEN' and r_multiple >= settings.BE_TRIGGER_R:
                self.move_to_break_even(position, current_price)
            
            # Check for Partial TP
            if not position.partial_closed and r_multiple >= settings.PARTIAL_TP_R:
                self.execute_partial_tp(position, current_price)
            
            # Check for Trailing Stop activation
            if r_multiple >= settings.TRAILING_ACTIVATION_R:
                self.update_trailing_stop(position, current_price)
            
        except Exception as e:
            logger.error(f"Error managing position {position.pair}: {e}")
    
    def sync_with_exchange(self):
        """
        Sync local database with Binance positions
        """
        try:
            # 1. Get all positions from Binance
            exchange_positions = self.futures_client.get_all_positions()
            active_exchange_pairs = {}
            
            for ep in exchange_positions:
                amt = float(ep.get('positionAmt', 0))
                if abs(amt) > 0:
                    pair = self.futures_client.to_ccxt_symbol(ep['symbol'])
                    active_exchange_pairs[pair] = ep

            # 2. Update local database
            db = SessionLocal()
            try:
                # Get all locally active positions
                local_positions = db.query(Position).filter(
                    Position.status.in_(['OPEN', 'BE', 'TRAILING'])
                ).all()
                
                # Close local positions that are no longer on exchange
                for lp in local_positions:
                    if lp.pair not in active_exchange_pairs:
                        logger.info(f"Position {lp.pair} not found on exchange, closing locally")
                        lp.status = 'CLOSED'
                        lp.closed_at = datetime.now()
                
                # Add exchange positions that are missing locally
                for pair, ep in active_exchange_pairs.items():
                    exists = any(lp.pair == pair for lp in local_positions)
                    if not exists:
                        logger.info(f"Syncing new position from exchange: {pair}")
                        amt = float(ep['positionAmt'])
                        side = 'LONG' if amt > 0 else 'SHORT'
                        
                        new_pos = Position(
                            pair=pair,
                            side=side,
                            entry_price=Decimal(str(ep['entryPrice'])),
                            sl_price=Decimal("0"), # Unknown SL
                            tp_price=Decimal("0"), # Unknown TP
                            quantity=Decimal(str(abs(amt))),
                            leverage=int(ep['leverage']),
                            status='OPEN',
                            ai_reason="Synced from exchange",
                            pnl=Decimal(str(ep['unRealizedProfit']))
                        )
                        db.add(new_pos)
                
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"Error during sync commit: {e}")
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error syncing with exchange: {e}")

    def manage_all_positions(self):
        """
        Manage all active positions
        """
        try:
            # First sync with exchange
            self.sync_with_exchange()
            
            positions = self.get_active_positions()
            
            if not positions:
                logger.debug("No active positions to manage")
                return
            
            logger.debug(f"Managing {len(positions)} active positions...")
            
            for position in positions:
                self.manage_position(position)
            
        except Exception as e:
            logger.error(f"Error managing positions: {e}")



if __name__ == "__main__":
    # Test position manager
    logging.basicConfig(level=logging.INFO)
    
    manager = PositionManager()
    manager.manage_all_positions()
