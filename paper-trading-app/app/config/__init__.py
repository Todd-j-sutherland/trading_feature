"""Configuration package initialization"""

from .settings import Settings
from .logging import setup_logging

# Basic trading config for IG Markets integration
TRADING_CONFIG = {
    "ig_markets_enabled": True,
    "fallback_to_yfinance": True,
    "default_symbols": ["CBA.AX", "WBC.AX", "ANZ.AX", "NAB.AX"],
    "price_cache_ttl": 60,
    "health_check_interval": 300
}

# Basic risk config
RISK_CONFIG = {
    "max_position_size": 10000,
    "max_daily_trades": 10,
    "stop_loss_percent": 5.0,
    "take_profit_percent": 10.0
}

__all__ = ["Settings", "setup_logging", "TRADING_CONFIG", "RISK_CONFIG"]
