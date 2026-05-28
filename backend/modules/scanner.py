"""
Market Scanner - Filter trading pairs based on volume and volatility
"""
import ccxt
import logging
from typing import List, Dict
from config import settings
from modules.binance_futures import BinanceFuturesClient

logger = logging.getLogger(__name__)


class MarketScanner:
    def __init__(self):
        """Initialize Binance exchange connection"""
        self.testnet_mode = settings.BINANCE_TESTNET
        self.futures_client = BinanceFuturesClient(self.testnet_mode)
        
        # For simulation mode, use public API only (no auth needed)
        if self.testnet_mode:
            self.exchange = ccxt.binance({
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future',
                }
            })
            
            logger.info("Market Scanner initialized in DEMO mode")
        else:
            self.exchange = ccxt.binance({
                'apiKey': settings.BINANCE_API_KEY,
                'secret': settings.BINANCE_SECRET_KEY,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future',
                }
            })
            logger.info("Market Scanner initialized in LIVE mode")
    
    def get_candidate_pairs(self) -> List[str]:
        """
        Hardcoded to return only Bitcoin for focused 15m trading strategy.
        """
        logger.info("Market Scanner: Locked to BTC/USDT:USDT only.")
        return ['BTC/USDT:USDT']

    def _fetch_tickers(self) -> Dict:
        if not self.testnet_mode:
            return self.exchange.fetch_tickers()

        tickers = {}
        for ticker in self.futures_client.get_24h_tickers():
            symbol = self.futures_client.to_ccxt_symbol(ticker.get('symbol', ''))
            tickers[symbol] = {
                'quoteVolume': float(ticker.get('quoteVolume', 0) or 0),
                'high': float(ticker.get('highPrice', 0) or 0),
                'low': float(ticker.get('lowPrice', 0) or 0),
                'close': float(ticker.get('lastPrice', 0) or 0),
                'last': float(ticker.get('lastPrice', 0) or 0),
            }
        return tickers
    
    def get_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> List:
        """
        Fetch OHLCV data for technical analysis
        
        Args:
            symbol: Trading pair symbol
            timeframe: Candle timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of candles
            
        Returns:
            List of OHLCV data
        """
        try:
            if self.testnet_mode:
                return self.futures_client.get_ohlcv(symbol, timeframe, limit)

            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            return ohlcv
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {e}")
            return []
    
    def get_ticker(self, symbol: str) -> Dict:
        """
        Get current ticker data for a symbol
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Ticker data dictionary
        """
        try:
            if self.testnet_mode:
                price = self.futures_client.get_price(symbol)
                return {'symbol': symbol, 'last': price, 'close': price}

            ticker = self.exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            return {}


if __name__ == "__main__":
    # Test scanner
    logging.basicConfig(level=logging.INFO)
    scanner = MarketScanner()
    pairs = scanner.get_candidate_pairs()
    print(f"\nCandidate pairs: {pairs}")
