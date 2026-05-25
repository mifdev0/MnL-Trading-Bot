"""
Configuration module - Load environment variables
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

# Get root directory (parent of backend folder)
ROOT_DIR = Path(__file__).parent.parent
ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseSettings):
    # Binance
    BINANCE_API_KEY: str
    BINANCE_SECRET_KEY: str
    # True uses Binance demo trading via ccxt enable_demo_trading, not deprecated futures testnet/sandbox.
    BINANCE_TESTNET: bool = True
    
    # AI Providers (use either one)
    ANTHROPIC_API_KEY: Optional[str] = "dummy_key"
    DEEPSEEK_API_KEY: Optional[str] = "dummy_key"
    GEMINI_API_KEY: Optional[str] = "dummy_key"
    
    # News APIs
    CRYPTOPANIC_API_KEY: str
    NEWSAPI_KEY: str
    COINGECKO_API_KEY: str
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHAT_ID: str
    
    # Database
    DATABASE_URL: str
    
    # Trading Config
    RISK_PER_TRADE: float = 1.0
    MAX_OPEN_POSITIONS: int = 5
    MIN_VOLUME_24H: float = 50000000
    MIN_VOLATILITY: float = 2.0
    LEVERAGE: int = 10
    MAX_BALANCE_CAP: float = 40.0
    
    # Risk Management
    BE_TRIGGER_R: float = 1.0
    PARTIAL_TP_R: float = 2.0
    TRAILING_ACTIVATION_R: float = 2.0
    TRAILING_DISTANCE_R: float = 1.0
    BE_BUFFER_PCT: float = 0.1
    
    # Dashboard
    DASHBOARD_PORT: int = 3000
    API_PORT: int = 8000
    
    class Config:
        env_file = str(ENV_FILE)
        case_sensitive = True


# Global settings instance
settings = Settings()
