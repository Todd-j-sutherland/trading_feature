"""
ASX (Australian Securities Exchange) Market Configuration

This module contains all ASX-specific market settings including:
- Trading hours and market calendar
- Currency and settlement information  
- Regulatory requirements
- Market structure and characteristics
"""

from datetime import time, date
from typing import Dict, List, Any

# ASX Market Information
MARKET_INFO = {
    "exchange_name": "Australian Securities Exchange",
    "exchange_code": "ASX",
    "country": "Australia",
    "currency": "AUD",
    "timezone": "Australia/Sydney",
    "market_maker": True,
    "settlement_cycle": "T+2"  # Trade date plus 2 business days
}

# ASX Trading Hours (Australian Eastern Standard Time)
TRADING_HOURS = {
    "market_open": time(10, 0),      # 10:00 AM AEST
    "market_close": time(16, 0),     # 4:00 PM AEST
    "pre_market_open": time(7, 0),   # 7:00 AM AEST
    "pre_market_close": time(10, 0), # 10:00 AM AEST
    "after_hours_open": time(16, 10), # 4:10 PM AEST
    "after_hours_close": time(17, 0), # 5:00 PM AEST
    "timezone": "Australia/Sydney",
    "dst_adjustment": True
}

# ASX Market Sessions
MARKET_SESSIONS = {
    "pre_market": {
        "name": "Pre-Market",
        "start": "07:00",
        "end": "10:00",
        "description": "Pre-market single price auction"
    },
    "opening_auction": {
        "name": "Opening Auction",
        "start": "10:00",
        "end": "10:10", 
        "description": "Opening single price auction"
    },
    "continuous_trading": {
        "name": "Continuous Trading",
        "start": "10:10",
        "end": "16:00",
        "description": "Normal trading session"
    },
    "closing_auction": {
        "name": "Closing Auction", 
        "start": "16:00",
        "end": "16:10",
        "description": "Closing single price auction"
    },
    "after_hours": {
        "name": "After Hours",
        "start": "16:10", 
        "end": "17:00",
        "description": "Limited after-hours trading"
    }
}

# ASX Market Holidays (2024-2025)
MARKET_HOLIDAYS = [
    # 2024 Holidays
    date(2024, 1, 1),   # New Year's Day
    date(2024, 1, 26),  # Australia Day
    date(2024, 3, 29),  # Good Friday
    date(2024, 4, 1),   # Easter Monday
    date(2024, 4, 25),  # ANZAC Day
    date(2024, 6, 10),  # Queen's Birthday
    date(2024, 12, 25), # Christmas Day
    date(2024, 12, 26), # Boxing Day
    
    # 2025 Holidays  
    date(2025, 1, 1),   # New Year's Day
    date(2025, 1, 27),  # Australia Day (observed)
    date(2025, 4, 18),  # Good Friday
    date(2025, 4, 21),  # Easter Monday
    date(2025, 4, 25),  # ANZAC Day
    date(2025, 6, 9),   # Queen's Birthday
    date(2025, 12, 25), # Christmas Day
    date(2025, 12, 26)  # Boxing Day
]

# ASX Regulatory Information
REGULATORY_INFO = {
    "regulator": "Australian Securities and Investments Commission (ASIC)",
    "market_operator": "ASX Limited",
    "clearing_house": "ASX Clear Pty Limited",
    "settlement": "ASX Settlement Pty Limited",
    "regulations": {
        "continuous_disclosure": True,
        "insider_trading_rules": True,
        "market_manipulation_rules": True,
        "short_selling_allowed": True,
        "circuit_breakers": True
    }
}

# ASX Market Indices
MARKET_INDICES = {
    "ASX_200": {
        "symbol": "^AXJO",
        "name": "S&P/ASX 200",
        "description": "Market-capitalization weighted index of 200 largest ASX-listed companies",
        "base_date": "2000-03-31",
        "base_value": 3133.3
    },
    "ASX_300": {
        "symbol": "^AXKO", 
        "name": "S&P/ASX 300",
        "description": "Market-capitalization weighted index of 300 largest ASX-listed companies"
    },
    "ASX_50": {
        "symbol": "^AXTO",
        "name": "S&P/ASX 50", 
        "description": "Market-capitalization weighted index of 50 largest ASX-listed companies"
    },
    "ASX_SMALL_ORDS": {
        "symbol": "^AXSO",
        "name": "S&P/ASX Small Ordinaries",
        "description": "Small cap companies index"
    }
}

# ASX Sector Classifications (GICS)
SECTOR_CLASSIFICATIONS = {
    "banking": {
        "gics_code": "4010",
        "name": "Banks",
        "description": "Commercial banks, thrifts & mortgage finance and consumer finance"
    },
    "insurance": {
        "gics_code": "4020", 
        "name": "Insurance",
        "description": "Insurance companies including life, health, property & casualty"
    },
    "diversified_financials": {
        "gics_code": "4030",
        "name": "Diversified Financials", 
        "description": "Investment banking, asset management, securities brokerage"
    },
    "real_estate": {
        "gics_code": "4040",
        "name": "Real Estate",
        "description": "Real estate investment trusts and real estate management"
    }
}

# ASX Trading Rules and Limits
TRADING_RULES = {
    "minimum_tick_size": {
        "under_0_10": 0.001,     # $0.001 for prices under $0.10
        "0_10_to_2_00": 0.005,   # $0.005 for prices $0.10 to $2.00
        "over_2_00": 0.01        # $0.01 for prices over $2.00
    },
    "price_limits": {
        "circuit_breaker_5_percent": True,
        "circuit_breaker_10_percent": True,
        "maximum_daily_move": None  # No daily price limits
    },
    "order_types": [
        "market", "limit", "stop", "stop_limit", 
        "market_to_limit", "iceberg", "hidden"
    ],
    "settlement_currency": "AUD",
    "trade_reporting_required": True
}

# ASX Market Microstructure
MARKET_MICROSTRUCTURE = {
    "trading_mechanism": "continuous_double_auction",
    "order_priority": ["price", "time"],
    "tick_size_regime": "variable",
    "lot_size": 1,  # No minimum lot size
    "short_selling": {
        "allowed": True,
        "uptick_rule": False,
        "borrowing_required": True,
        "reporting_required": True
    },
    "dark_pools": True,
    "crossing_networks": True
}

# ASX Data Feed Configuration
DATA_FEEDS = {
    "real_time": {
        "provider": "ASX Market Data",
        "latency": "sub_millisecond",
        "cost": "premium"
    },
    "delayed": {
        "provider": "ASX Market Data", 
        "delay_minutes": 20,
        "cost": "free"
    },
    "end_of_day": {
        "provider": "ASX Market Data",
        "delivery_time": "17:30",
        "cost": "standard"
    }
}

# ASX Market Quality Metrics
MARKET_QUALITY = {
    "average_bid_ask_spread": {
        "large_cap": 0.001,    # 10 basis points
        "mid_cap": 0.002,      # 20 basis points
        "small_cap": 0.005     # 50 basis points
    },
    "market_impact": {
        "large_cap": "low",
        "mid_cap": "medium", 
        "small_cap": "high"
    },
    "liquidity_provision": "market_makers_and_ecns"
}

def get_market_status(current_time=None) -> str:
    """
    Determine current ASX market status
    Returns: 'pre_market', 'open', 'closed', 'after_hours'
    """
    from datetime import datetime
    import pytz
    
    if current_time is None:
        current_time = datetime.now(pytz.timezone(TRADING_HOURS["timezone"]))
    
    # Check if it's a weekend
    if current_time.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return "closed"
    
    # Check if it's a market holiday
    if current_time.date() in MARKET_HOLIDAYS:
        return "closed"
    
    current_time_only = current_time.time()
    
    if current_time_only < TRADING_HOURS["pre_market_open"]:
        return "closed"
    elif current_time_only < TRADING_HOURS["market_open"]:
        return "pre_market"
    elif current_time_only < TRADING_HOURS["market_close"]:
        return "open"
    elif current_time_only < TRADING_HOURS["after_hours_close"]:
        return "after_hours"
    else:
        return "closed"

def is_trading_day(check_date=None) -> bool:
    """Check if given date is a trading day"""
    from datetime import date as dt_date
    
    if check_date is None:
        check_date = dt_date.today()
    
    # Check if weekend
    if check_date.weekday() >= 5:
        return False
    
    # Check if holiday
    if check_date in MARKET_HOLIDAYS:
        return False
    
    return True

def get_next_trading_day(from_date=None) -> date:
    """Get the next trading day from given date"""
    from datetime import date as dt_date, timedelta
    
    if from_date is None:
        from_date = dt_date.today()
    
    next_day = from_date + timedelta(days=1)
    
    while not is_trading_day(next_day):
        next_day += timedelta(days=1)
    
    return next_day

def get_trading_calendar(year: int) -> List[date]:
    """Get list of all trading days for a given year"""
    from datetime import date as dt_date, timedelta
    
    trading_days = []
    current_date = dt_date(year, 1, 1)
    end_date = dt_date(year, 12, 31)
    
    while current_date <= end_date:
        if is_trading_day(current_date):
            trading_days.append(current_date)
        current_date += timedelta(days=1)
    
    return trading_days
