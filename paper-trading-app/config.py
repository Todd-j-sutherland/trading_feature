#!/usr/bin/env python3
"""
Configuration settings for Paper Trading App
"""

import os
from datetime import datetime

# Database Configuration
DATABASE_URL = "sqlite:///paper_trading.db"
DATABASE_PATH = "paper_trading.db"

# Account Configuration
DEFAULT_INITIAL_BALANCE = 100000.0  # $100,000 starting capital
DEFAULT_COMMISSION_RATE = 0.0       # 0% commission (configurable via dashboard)
DEFAULT_SLIPPAGE_RATE = 0.001       # 0.1% slippage

# Risk Management
MAX_POSITION_SIZE_PCT = 0.20        # Maximum 20% of portfolio in one position
DAILY_LOSS_LIMIT_PCT = 0.05         # Maximum 5% daily loss
MAX_PORTFOLIO_CONCENTRATION = 0.30   # Maximum 30% in one sector

# Configuration Dictionaries for compatibility
TRADING_CONFIG = {
    'initial_balance': DEFAULT_INITIAL_BALANCE,
    'commission_rate': DEFAULT_COMMISSION_RATE,
    'min_commission': 0.0,  # $0 minimum (configurable)
    'max_commission': 100.0,  # $100 maximum (configurable)
    'slippage_rate': DEFAULT_SLIPPAGE_RATE,
    # IG Markets integration settings
    'use_ig_markets': True,
    'ig_markets_priority': True,
    'price_source_timeout_seconds': 10
}

RISK_CONFIG = {
    'max_position_size': MAX_POSITION_SIZE_PCT,
    'daily_loss_limit': DAILY_LOSS_LIMIT_PCT,
    'max_concentration': MAX_PORTFOLIO_CONCENTRATION
}

MARKET_CONFIG = {
    'trading_hours': {
        'start': '09:30',
        'end': '16:00'
    },
    'timezone': 'US/Eastern'
}
MARGIN_REQUIREMENT = 0.25           # 25% margin requirement

# Trading Configuration
SUPPORTED_SYMBOLS = [
    'CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX', 'MQG.AX', 'SUN.AX', 'QBE.AX',
    'AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META', 'NVDA', 'AMD', 'INTC'
]

ASX_SYMBOLS = ['CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX', 'MQG.AX', 'SUN.AX', 'QBE.AX']
US_SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META', 'NVDA', 'AMD', 'INTC']

# Market Hours (for simulation)
ASX_MARKET_OPEN = "10:00"
ASX_MARKET_CLOSE = "16:00"
US_MARKET_OPEN = "09:30"
US_MARKET_CLOSE = "16:00"

# Performance Metrics
RISK_FREE_RATE = 0.04              # 4% risk-free rate for Sharpe ratio
TRADING_DAYS_PER_YEAR = 252

# Dashboard Configuration
DASHBOARD_TITLE = "Paper Trading Dashboard"
REFRESH_INTERVAL = 30               # Seconds between price updates
DEFAULT_CHART_PERIOD = "1mo"       # Default chart period

# Data Sources Configuration
PRICE_DATA_SOURCE = "enhanced_ig_markets"  # Use IG Markets integration
BACKUP_DATA_SOURCE = "yfinance"           # Fallback to yfinance
ENABLE_IG_MARKETS = True                   # Enable IG Markets integration

# IG Markets Integration Settings
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

# Data Sources
PRICE_DATA_SOURCE = "enhanced_ig_markets"  # Primary: IG Markets integration
BACKUP_DATA_SOURCE = "yfinance"           # Fallback: yfinance

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "paper_trading.log"

# Strategy Integration
STRATEGY_UPDATE_INTERVAL = 300      # 5 minutes between strategy updates
DEFAULT_POSITION_SIZE_METHOD = "fixed_dollar"  # or "kelly", "fixed_percent"
DEFAULT_POSITION_SIZE_VALUE = 10000  # $10,000 per position

# Export Configuration
EXPORT_PATH = "exports/"
BACKUP_PATH = "backups/"

# App Metadata
APP_VERSION = "1.0.0"
APP_AUTHOR = "Todd Sutherland"
CREATED_DATE = datetime.now().strftime("%Y-%m-%d")

# Development Configuration
DEBUG_MODE = True
MOCK_DATA_MODE = False              # Use mock data instead of real market data
SIMULATION_SPEED = 1.0              # 1.0 = real-time, 2.0 = 2x speed, etc.
