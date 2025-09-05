"""Configuration package initialization"""

from .settings import Settings
from .logging import setup_logging

# Trading Configuration for Paper Trading Integration
TRADING_CONFIG = {
    'initial_balance': 100000.0,
    'commission_rate': 0.0,
    'min_commission': 0.0,
    'max_commission': 100.0,
    'slippage_rate': 0.001,
    # IG Markets integration settings
    'use_ig_markets': True,
    'ig_markets_priority': True,
    'price_source_timeout_seconds': 10,
    # Risk management
    'max_position_size_pct': 0.20,
    'daily_loss_limit_pct': 0.05,
    'max_portfolio_concentration': 0.30
}

# Risk Management Configuration
RISK_CONFIG = {
    'max_position_size': 0.20,
    'daily_loss_limit': 0.05,
    'max_concentration': 0.30,
    'margin_requirement': 0.25,
    'stop_loss_pct': 0.10,
    'take_profit_pct': 0.20
}

# IG Markets Configuration
IG_MARKETS_CONFIG = {
    'enabled': True,
    'fallback_to_yfinance': True,
    'cache_duration_minutes': 5,
    'health_check_interval_seconds': 600,
    'log_usage_stats': True,
    'preferred_symbols': [
        'CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX',
        'BHP.AX', 'RIO.AX', 'CSL.AX', 'TLS.AX'
    ]
}

# Market Configuration
MARKET_CONFIG = {
    'trading_hours': {
        'start': '09:30',
        'end': '16:00'
    },
    'timezone': 'US/Eastern',
    'supported_symbols': [
        'CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX', 'MQG.AX', 'SUN.AX', 'QBE.AX'
    ]
}
