"""
USA Financial Markets Configuration

This module contains comprehensive USA market settings including NYSE, NASDAQ, and other US exchanges.
Focus on US banking sector and major financial institutions.
"""

from datetime import datetime, time
from typing import Dict, List, Any
import pytz

# USA Market Configuration
MARKET_CONFIG = {
    "market_name": "United States Financial Markets",
    "primary_exchanges": ["NYSE", "NASDAQ", "AMEX"],
    "currency": "USD",
    "timezone": "America/New_York",
    "country_code": "US",
    "market_type": "developed",
    
    # Market structure
    "market_structure": {
        "lot_size": 1,  # Shares
        "tick_size": 0.01,  # $0.01 minimum price increment
        "settlement_cycle": "T+2",  # 2 business days
        "trading_unit": "shares",
        "decimal_places": 2
    },
    
    # Trading sessions
    "sessions": {
        "pre_market": {
            "start": "04:00",
            "end": "09:30",
            "description": "Extended hours trading"
        },
        "regular": {
            "start": "09:30", 
            "end": "16:00",
            "description": "Regular trading session"
        },
        "after_hours": {
            "start": "16:00",
            "end": "20:00", 
            "description": "After-hours trading"
        }
    },
    
    # Market characteristics
    "characteristics": {
        "high_liquidity": True,
        "high_volatility": True,
        "sophisticated_participants": True,
        "algorithmic_trading_heavy": True,
        "global_market_leader": True
    }
}

# USA Trading Hours (Eastern Time)
TRADING_HOURS = {
    "timezone": "America/New_York",
    "regular_session": {
        "open": "09:30",
        "close": "16:00",
        "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    },
    "extended_hours": {
        "pre_market": {
            "start": "04:00",
            "end": "09:30"
        },
        "after_hours": {
            "start": "16:00", 
            "end": "20:00"
        }
    },
    "lunch_break": None,  # No lunch break in US markets
    "early_close_time": "13:00",  # Some holidays
    
    # Daylight saving time adjustments
    "dst_adjustments": {
        "spring_forward": "Second Sunday in March",
        "fall_back": "First Sunday in November",
        "note": "Market hours remain constant in ET, but UTC offset changes"
    }
}

# USA Market Holidays (2024)
MARKET_HOLIDAYS = {
    "2024": [
        "2024-01-01",  # New Year's Day
        "2024-01-15",  # Martin Luther King Jr. Day
        "2024-02-19",  # Presidents' Day
        "2024-03-29",  # Good Friday
        "2024-05-27",  # Memorial Day
        "2024-06-19",  # Juneteenth National Independence Day
        "2024-07-04",  # Independence Day
        "2024-09-02",  # Labor Day
        "2024-11-28",  # Thanksgiving Day
        "2024-12-25"   # Christmas Day
    ],
    "early_close_days": [
        "2024-07-03",   # Day before Independence Day
        "2024-11-29",   # Day after Thanksgiving
        "2024-12-24"    # Christmas Eve
    ],
    "note": "Markets close at 1:00 PM ET on early close days"
}

# US Regulatory Information
REGULATORY_INFO = {
    "primary_regulator": "SEC",  # Securities and Exchange Commission
    "banking_regulator": "Federal Reserve",
    "additional_regulators": ["FINRA", "CFTC", "OCC", "FDIC"],
    
    "regulatory_framework": {
        "securities_act": "Securities Act of 1933",
        "exchange_act": "Securities Exchange Act of 1934", 
        "investment_company_act": "Investment Company Act of 1940",
        "dodd_frank": "Dodd-Frank Wall Street Reform Act",
        "mifid_equivalent": None  # US has own regulations
    },
    
    "disclosure_requirements": {
        "insider_trading": "Form 4 within 2 business days",
        "major_shareholding": "13D/13G filings",
        "earnings_guidance": "8-K filings",
        "annual_reports": "10-K filings",
        "quarterly_reports": "10-Q filings"
    },
    
    "market_surveillance": {
        "circuit_breakers": True,
        "limit_up_limit_down": True,
        "trading_halts": True,
        "short_sale_restrictions": True
    }
}

# USA Market Indices
MARKET_INDICES = {
    "major_indices": {
        "SP500": {
            "name": "S&P 500",
            "symbol": "SPY",
            "description": "500 largest US companies",
            "weight_method": "market_cap_weighted"
        },
        "NASDAQ": {
            "name": "NASDAQ Composite",
            "symbol": "QQQ",
            "description": "Technology-heavy index",
            "weight_method": "market_cap_weighted"
        },
        "DJIA": {
            "name": "Dow Jones Industrial Average",
            "symbol": "DIA", 
            "description": "30 large industrial companies",
            "weight_method": "price_weighted"
        },
        "RUSSELL2000": {
            "name": "Russell 2000",
            "symbol": "IWM",
            "description": "Small-cap index",
            "weight_method": "market_cap_weighted"
        }
    },
    
    "financial_sector_indices": {
        "XLF": {
            "name": "Financial Select Sector SPDR Fund",
            "description": "S&P 500 financial sector",
            "focus": "broad_financial"
        },
        "KRE": {
            "name": "SPDR S&P Regional Banking ETF", 
            "description": "Regional banks",
            "focus": "regional_banks"
        },
        "KBE": {
            "name": "SPDR S&P Bank ETF",
            "description": "Banking sector",
            "focus": "banks"
        }
    }
}

# US Financial Sector Classifications
SECTOR_CLASSIFICATIONS = {
    "GICS_sectors": {
        "Financials": {
            "code": "40",
            "sub_sectors": [
                "Banks",
                "Diversified Financial Services", 
                "Insurance",
                "Capital Markets",
                "Mortgage Real Estate Investment Trusts (REITs)",
                "Consumer Finance"
            ]
        }
    },
    
    "banking_categories": {
        "money_center_banks": [
            "Large multinational banks with significant trading operations"
        ],
        "regional_banks": [
            "Banks primarily serving specific geographic regions"
        ],
        "community_banks": [
            "Smaller banks serving local communities"
        ],
        "investment_banks": [
            "Banks focused on capital markets and advisory services"
        ]
    },
    
    "bank_size_categories": {
        "systemically_important": {
            "description": "G-SIBs - Global Systemically Important Banks",
            "asset_threshold": ">$250B",
            "additional_regulation": "Enhanced prudential standards"
        },
        "large_regional": {
            "description": "Large regional and super-regional banks",
            "asset_threshold": "$50B-$250B"
        },
        "mid_size": {
            "description": "Mid-size regional banks",
            "asset_threshold": "$10B-$50B"
        },
        "community": {
            "description": "Community banks",
            "asset_threshold": "<$10B"
        }
    }
}

# US Trading Rules and Regulations
TRADING_RULES = {
    "pattern_day_trading": {
        "minimum_equity": 25000,  # $25K USD
        "rule": "Must maintain $25K in account if executing 4+ day trades in 5 business days"
    },
    
    "settlement_rules": {
        "cash_accounts": "T+2 settlement",
        "margin_accounts": "Immediate buying power",
        "good_faith_violations": "Buying and selling before settlement in cash account"
    },
    
    "short_selling": {
        "uptick_rule": "Modified uptick rule in effect",
        "locate_requirement": "Must locate shares before shorting",
        "circuit_breaker": "Short sale restrictions triggered by 10% decline"
    },
    
    "market_orders": {
        "regular_hours": "9:30 AM - 4:00 PM ET",
        "extended_hours": "Limited order types available",
        "minimum_price_increment": 0.01
    },
    
    "position_limits": {
        "retail_investors": "No specific limits for most stocks",
        "institutional": "Must disclose 5%+ positions",
        "insider_restrictions": "Blackout periods around earnings"
    }
}

# Currency and Economic Factors
CURRENCY_INFO = {
    "currency": "USD",
    "symbol": "$",
    "decimal_places": 2,
    "is_reserve_currency": True,
    
    "major_currency_pairs": [
        "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "USD/CAD", "AUD/USD"
    ],
    
    "economic_indicators": {
        "central_bank": "Federal Reserve (Fed)",
        "key_rate": "Federal Funds Rate",
        "inflation_target": "2.0%",
        "major_economic_releases": [
            "Non-Farm Payrolls",
            "CPI/PCE Inflation",
            "GDP",
            "FOMC Meetings",
            "Retail Sales",
            "Industrial Production"
        ]
    },
    
    "market_impact_factors": [
        "Federal Reserve policy",
        "Treasury yield movements", 
        "Dollar strength/weakness",
        "Economic data releases",
        "Geopolitical events"
    ]
}

# Market Microstructure
MARKET_MICROSTRUCTURE = {
    "order_types": [
        "Market", "Limit", "Stop", "Stop-Limit", 
        "Fill-or-Kill", "All-or-None", "Immediate-or-Cancel"
    ],
    
    "execution_venues": [
        "NYSE", "NASDAQ", "BATS", "IEX", "Dark Pools"
    ],
    
    "market_makers": {
        "designated_market_makers": "NYSE specialists",
        "electronic_market_makers": "High-frequency trading firms",
        "obligation": "Provide liquidity during trading hours"
    },
    
    "tick_sizes": {
        "stocks_above_1": 0.01,
        "stocks_below_1": 0.0001,
        "special_securities": "Varies by security type"
    },
    
    "circuit_breakers": {
        "level_1": "7% market decline - 15 minute halt",
        "level_2": "13% market decline - 15 minute halt", 
        "level_3": "20% market decline - trading halted for day",
        "individual_stock": "10% move in 5 minutes triggers halt"
    }
}

def get_current_trading_session() -> str:
    """Get current trading session based on ET time"""
    et_tz = pytz.timezone("America/New_York")
    current_time = datetime.now(et_tz).time()
    
    pre_market_start = time(4, 0)
    regular_start = time(9, 30)
    regular_end = time(16, 0)
    after_hours_end = time(20, 0)
    
    if pre_market_start <= current_time < regular_start:
        return "pre_market"
    elif regular_start <= current_time < regular_end:
        return "regular"
    elif regular_end <= current_time < after_hours_end:
        return "after_hours"
    else:
        return "closed"

def is_market_holiday(check_date: datetime = None) -> bool:
    """Check if given date is a US market holiday"""
    if check_date is None:
        check_date = datetime.now()
    
    date_str = check_date.strftime("%Y-%m-%d")
    year = str(check_date.year)
    
    holidays = MARKET_HOLIDAYS.get(year, [])
    return date_str in holidays

def is_early_close_day(check_date: datetime = None) -> bool:
    """Check if given date is an early close day"""
    if check_date is None:
        check_date = datetime.now()
    
    date_str = check_date.strftime("%Y-%m-%d") 
    year = str(check_date.year)
    
    early_close_days = MARKET_HOLIDAYS.get("early_close_days", [])
    return date_str in early_close_days

def get_market_status() -> Dict[str, Any]:
    """Get comprehensive market status"""
    et_tz = pytz.timezone("America/New_York")
    now = datetime.now(et_tz)
    
    return {
        "current_time_et": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "trading_session": get_current_trading_session(),
        "is_trading_day": now.weekday() < 5,  # Monday = 0, Friday = 4
        "is_holiday": is_market_holiday(now),
        "is_early_close": is_early_close_day(now),
        "market_open": get_current_trading_session() == "regular"
    }
