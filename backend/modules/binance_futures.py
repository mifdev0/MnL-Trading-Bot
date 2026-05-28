"""
Binance Futures REST client for demo/testnet-safe execution.
"""
import hashlib
import hmac
import logging
import time
from decimal import Decimal, ROUND_DOWN
from urllib.parse import urlencode

import requests
import urllib3

from config import settings

logger = logging.getLogger(__name__)


class BinanceFuturesClient:
    def __init__(self, demo_mode: bool = True):
        self.demo_mode = demo_mode
        # Binance has 3 environments now:
        # 1. LIVE: fapi.binance.com
        # 2. NEW DEMO: demo-api.binance.com (Keys usually start with 'demo_')
        # 3. OLD TESTNET: testnet.binancefuture.com (Standalone site)
        
        if not demo_mode:
            self.base_url = "https://fapi.binance.com"
        elif settings.BINANCE_API_KEY.startswith("demo_"):
            self.base_url = "https://demo-api.binance.com"
        else:
            # Fallback to standalone testnet for legacy keys
            self.base_url = "https://testnet.binancefuture.com"
            
        logger.info(f"Binance Futures Client initialized with base URL: {self.base_url}")
        self.verify_ssl = True
        self._exchange_info = None

        if "testnet" in self.base_url:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            self.verify_ssl = False

    def to_market_symbol(self, symbol: str) -> str:
        return symbol.split(":")[0].replace("/", "")

    def to_ccxt_symbol(self, market_symbol: str) -> str:
        if market_symbol.endswith("USDT"):
            return f"{market_symbol[:-4]}/USDT:USDT"
        return market_symbol

    def public_get(self, path: str, params: dict | None = None):
        response = requests.get(
            f"{self.base_url}{path}",
            params=params or {},
            timeout=15,
            verify=self.verify_ssl,
        )
        response.raise_for_status()
        return response.json()

    def signed_request(self, method: str, path: str, params: dict | None = None):
        params = dict(params or {})
        params["timestamp"] = int(time.time() * 1000)
        query = urlencode(params)
        signature = hmac.new(
            settings.BINANCE_SECRET_KEY.encode(),
            query.encode(),
            hashlib.sha256,
        ).hexdigest()
        url = f"{self.base_url}{path}?{query}&signature={signature}"
        response = requests.request(
            method,
            url,
            headers={"X-MBX-APIKEY": settings.BINANCE_API_KEY},
            timeout=20,
            verify=self.verify_ssl,
        )

        try:
            payload = response.json()
        except ValueError:
            payload = response.text

        if response.status_code >= 400:
            raise RuntimeError(f"Binance {method} {path} failed: {response.status_code} {payload}")

        if isinstance(payload, dict):
            code = payload.get("code")
            if code is not None:
                try:
                    if int(code) < 0:
                        raise RuntimeError(f"Binance {method} {path} failed: {payload}")
                except (ValueError, TypeError):
                    pass

        return payload

    def exchange_info(self) -> dict:
        if self._exchange_info is None:
            self._exchange_info = self.public_get("/fapi/v1/exchangeInfo")
        return self._exchange_info

    def symbol_info(self, symbol: str) -> dict:
        market_symbol = self.to_market_symbol(symbol)
        for item in self.exchange_info().get("symbols", []):
            if item.get("symbol") == market_symbol:
                return item
        raise ValueError(f"Symbol not found on Binance Futures: {symbol}")

    def _filter_value(self, symbol: str, filter_type: str, key: str) -> Decimal:
        for item in self.symbol_info(symbol).get("filters", []):
            if item.get("filterType") == filter_type:
                return Decimal(str(item[key]))
        raise ValueError(f"Filter {filter_type}.{key} not found for {symbol}")

    def _floor_to_step(self, value, step: Decimal) -> Decimal:
        value = Decimal(str(value))
        if step == 0:
            return value
        return (value / step).to_integral_value(rounding=ROUND_DOWN) * step

    def format_quantity(self, symbol: str, quantity) -> str:
        step = self._filter_value(symbol, "LOT_SIZE", "stepSize")
        min_qty = self._filter_value(symbol, "LOT_SIZE", "minQty")
        formatted = self._floor_to_step(quantity, step)
        if formatted < min_qty:
            raise ValueError(f"Quantity {formatted} below minQty {min_qty} for {symbol}")
        return format(formatted.normalize(), "f")

    def format_price(self, symbol: str, price) -> str:
        tick = self._filter_value(symbol, "PRICE_FILTER", "tickSize")
        formatted = self._floor_to_step(price, tick)
        return format(formatted.normalize(), "f")

    def get_balance(self) -> dict:
        account = self.signed_request("GET", "/fapi/v2/account")
        return {
            "total": float(account["totalWalletBalance"]),
            "free": float(account["availableBalance"]),
            "used": float(account["totalInitialMargin"]),
        }

    def get_price(self, symbol: str) -> float:
        data = self.public_get(
            "/fapi/v1/ticker/price",
            {"symbol": self.to_market_symbol(symbol)},
        )
        return float(data["price"])

    def get_position(self, symbol: str) -> dict | None:
        market_symbol = self.to_market_symbol(symbol)
        positions = self.signed_request("GET", "/fapi/v2/positionRisk", {"symbol": market_symbol})
        for position in positions:
            if position.get("symbol") == market_symbol:
                return position
        return None

    def get_all_positions(self) -> list:
        return self.signed_request("GET", "/fapi/v2/positionRisk")

    def set_leverage(self, symbol: str, leverage: int) -> dict:
        return self.signed_request(
            "POST",
            "/fapi/v1/leverage",
            {"symbol": self.to_market_symbol(symbol), "leverage": leverage},
        )

    def create_market_order(self, symbol: str, side: str, quantity, reduce_only: bool = False) -> dict:
        params = {
            "symbol": self.to_market_symbol(symbol),
            "side": side.upper(),
            "type": "MARKET",
            "quantity": self.format_quantity(symbol, quantity),
        }
        if reduce_only:
            params["reduceOnly"] = "true"

        data = self.signed_request("POST", "/fapi/v1/order", params)
        return {"id": str(data["orderId"]), "raw": data}

    def create_close_algo_order(self, symbol: str, side: str, order_type: str, trigger_price) -> dict:
        data = self.signed_request(
            "POST",
            "/fapi/v1/algoOrder",
            {
                "symbol": self.to_market_symbol(symbol),
                "side": side.upper(),
                "type": order_type.upper(),
                "algoType": "CONDITIONAL",
                "triggerPrice": self.format_price(symbol, trigger_price),
                "closePosition": "true",
                "workingType": "MARK_PRICE",
            },
        )
        return {"id": f"ALGO_{data['algoId']}", "raw": data}

    def cancel_order(self, symbol: str, order_id: str):
        if not order_id:
            return None

        market_symbol = self.to_market_symbol(symbol)
        if str(order_id).startswith("ALGO_"):
            return self.signed_request(
                "DELETE",
                "/fapi/v1/algoOrder",
                {"symbol": market_symbol, "algoId": str(order_id).replace("ALGO_", "", 1)},
            )

        return self.signed_request(
            "DELETE",
            "/fapi/v1/order",
            {"symbol": market_symbol, "orderId": order_id},
        )

    def get_24h_tickers(self) -> list:
        return self.public_get("/fapi/v1/ticker/24hr")

    def get_ohlcv(self, symbol: str, timeframe: str = "1h", limit: int = 100) -> list:
        interval = timeframe
        klines = self.public_get(
            "/fapi/v1/klines",
            {"symbol": self.to_market_symbol(symbol), "interval": interval, "limit": limit},
        )
        return [
            [
                int(k[0]),
                float(k[1]),
                float(k[2]),
                float(k[3]),
                float(k[4]),
                float(k[5]),
            ]
            for k in klines
        ]
