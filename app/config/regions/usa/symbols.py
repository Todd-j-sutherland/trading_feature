"""
USA Financial Sector Symbols Configuration

This module contains comprehensive US financial sector symbols organized by categories.
Focus on major US banks, investment banks, and financial institutions.
"""

from typing import Dict, List, Any
from datetime import datetime

# Primary USA Financial Sector Symbols (Core Trading Focus)
FINANCIAL_SECTOR_SYMBOLS = {
    # Major US Banks (Primary Focus)
    "major_banks": {
        "JPM": {
            "name": "JPMorgan Chase & Co.",
            "sector": "Money Center Banks",
            "market_cap_tier": "mega_cap",
            "index_membership": ["SP500", "DJIA"],
            "priority": "high",
            "trading_priority": 1,
            "liquidity": "very_high",
            "volatility": "medium",
            "dividend_yield_range": [2.5, 4.0],
            "pe_ratio_range": [10, 16],
            "beta_range": [1.0, 1.4],
            "business_type": "universal_bank",
            "regulatory_classification": "G-SIB",  # Global Systemically Important Bank
            "headquarters": "New York, NY",
            "exchange": "NYSE"
        },
        "BAC": {
            "name": "Bank of America Corporation",
            "sector": "Money Center Banks",
            "market_cap_tier": "mega_cap",
            "index_membership": ["SP500", "DJIA"],
            "priority": "high",
            "trading_priority": 2,
            "liquidity": "very_high",
            "volatility": "medium",
            "dividend_yield_range": [2.0, 3.5],
            "pe_ratio_range": [8, 15],
            "beta_range": [1.1, 1.5],
            "business_type": "universal_bank",
            "regulatory_classification": "G-SIB",
            "headquarters": "Charlotte, NC",
            "exchange": "NYSE"
        },
        "WFC": {
            "name": "Wells Fargo & Company",
            "sector": "Money Center Banks",
            "market_cap_tier": "large_cap",
            "index_membership": ["SP500", "DJIA"],
            "priority": "high",
            "trading_priority": 3,
            "liquidity": "very_high",
            "volatility": "medium-high",
            "dividend_yield_range": [2.5, 4.5],
            "pe_ratio_range": [9, 16],
            "beta_range": [1.0, 1.4],
            "business_type": "commercial_bank",
            "regulatory_classification": "G-SIB",
            "headquarters": "San Francisco, CA",
            "exchange": "NYSE"
        },
        "C": {
            "name": "Citigroup Inc.",
            "sector": "Money Center Banks",
            "market_cap_tier": "large_cap",
            "index_membership": ["SP500"],
            "priority": "high",
            "trading_priority": 4,
            "liquidity": "very_high",
            "volatility": "high",
            "dividend_yield_range": [3.0, 5.0],
            "pe_ratio_range": [7, 14],
            "beta_range": [1.2, 1.7],
            "business_type": "global_bank",
            "regulatory_classification": "G-SIB",
            "headquarters": "New York, NY",
            "exchange": "NYSE"
        }
    },
    
    # Investment Banks & Broker-Dealers
    "investment_banks": {
        "GS": {
            "name": "The Goldman Sachs Group, Inc.",
            "sector": "Investment Banking & Brokerage",
            "market_cap_tier": "large_cap",
            "index_membership": ["SP500", "DJIA"],
            "priority": "high",
            "trading_priority": 5,
            "liquidity": "high",
            "volatility": "high",
            "dividend_yield_range": [1.5, 3.0],
            "pe_ratio_range": [8, 18],
            "beta_range": [1.2, 1.8],
            "business_type": "investment_bank",
            "regulatory_classification": "G-SIB",
            "headquarters": "New York, NY",
            "exchange": "NYSE"
        },
        "MS": {
            "name": "Morgan Stanley",
            "sector": "Investment Banking & Brokerage",
            "market_cap_tier": "large_cap",
            "index_membership": ["SP500"],
            "priority": "high",
            "trading_priority": 6,
            "liquidity": "high",
            "volatility": "high",
            "dividend_yield_range": [2.0, 4.0],
            "pe_ratio_range": [10, 18],
            "beta_range": [1.1, 1.6],
            "business_type": "investment_bank_wealth_mgmt",
            "regulatory_classification": "G-SIB",
            "headquarters": "New York, NY",
            "exchange": "NYSE"
        },
        "SCHW": {
            "name": "The Charles Schwab Corporation",
            "sector": "Investment Banking & Brokerage",
            "market_cap_tier": "large_cap",
            "index_membership": ["SP500"],
            "priority": "medium",
            "trading_priority": 10,
            "liquidity": "high",
            "volatility": "medium",
            "dividend_yield_range": [1.0, 2.5],
            "pe_ratio_range": [12, 25],
            "beta_range": [1.0, 1.4],
            "business_type": "discount_brokerage_wealth_mgmt",
            "regulatory_classification": "Large Bank",
            "headquarters": "Westlake, TX",
            "exchange": "NYSE"
        }
    },
    
    # Regional Banks
    "regional_banks": {
        "USB": {
            "name": "U.S. Bancorp",
            "sector": "Regional Banks",
            "market_cap_tier": "large_cap",
            "index_membership": ["SP500"],
            "priority": "medium",
            "trading_priority": 8,
            "liquidity": "high",
            "volatility": "medium",
            "dividend_yield_range": [3.0, 5.0],
            "pe_ratio_range": [10, 18],
            "beta_range": [0.9, 1.3],
            "business_type": "regional_bank",
            "regulatory_classification": "Large Bank",
            "headquarters": "Minneapolis, MN",
            "exchange": "NYSE"
        },
        "PNC": {
            "name": "The PNC Financial Services Group, Inc.",
            "sector": "Regional Banks",
            "market_cap_tier": "large_cap",
            "index_membership": ["SP500"],
            "priority": "medium",
            "trading_priority": 9,
            "liquidity": "high",
            "volatility": "medium",
            "dividend_yield_range": [3.5, 5.5],
            "pe_ratio_range": [9, 16],
            "beta_range": [1.0, 1.4],
            "business_type": "regional_bank",
            "regulatory_classification": "Large Bank",
            "headquarters": "Pittsburgh, PA",
            "exchange": "NYSE"
        },
        "TFC": {
            "name": "Truist Financial Corporation",
            "sector": "Regional Banks",
            "market_cap_tier": "large_cap",
            "index_membership": ["SP500"],
            "priority": "medium",
            "trading_priority": 11,
            "liquidity": "medium-high",
            "volatility": "medium",
            "dividend_yield_range": [4.0, 6.0],
            "pe_ratio_range": [8, 15],
            "beta_range": [1.1, 1.5],
            "business_type": "regional_bank",
            "regulatory_classification": "Large Bank",
            "headquarters": "Charlotte, NC",
            "exchange": "NYSE"
        },
        "COF": {
            "name": "Capital One Financial Corporation",
            "sector": "Consumer Finance",
            "market_cap_tier": "large_cap",
            "index_membership": ["SP500"],
            "priority": "medium",
            "trading_priority": 12,
            "liquidity": "medium-high",
            "volatility": "high",
            "dividend_yield_range": [1.5, 3.5],
            "pe_ratio_range": [5, 12],
            "beta_range": [1.3, 1.8],
            "business_type": "consumer_finance_bank",
            "regulatory_classification": "Large Bank",
            "headquarters": "McLean, VA",
            "exchange": "NYSE"
        }
    },
    
    # Insurance Companies
    "insurance": {
        "BRK.B": {
            "name": "Berkshire Hathaway Inc. Class B",
            "sector": "Multi-line Insurance",
            "market_cap_tier": "mega_cap",
            "index_membership": ["SP500"],
            "priority": "medium",
            "trading_priority": 15,
            "liquidity": "high",
            "volatility": "medium",
            "dividend_yield_range": [0.0, 0.0],  # No dividend
            "pe_ratio_range": [12, 25],
            "beta_range": [0.8, 1.2],
            "business_type": "insurance_conglomerate",
            "regulatory_classification": "Insurance Company",
            "headquarters": "Omaha, NE",
            "exchange": "NYSE"
        },
        "AIG": {
            "name": "American International Group, Inc.",
            "sector": "Multi-line Insurance",
            "market_cap_tier": "large_cap",
            "index_membership": ["SP500"],
            "priority": "low",
            "trading_priority": 20,
            "liquidity": "medium",
            "volatility": "high",
            "dividend_yield_range": [2.0, 4.0],
            "pe_ratio_range": [8, 20],
            "beta_range": [1.2, 1.8],
            "business_type": "general_insurance",
            "regulatory_classification": "Insurance Company",
            "headquarters": "New York, NY",
            "exchange": "NYSE"
        }
    },
    
    # Asset Management & Specialty Finance
    "asset_management": {
        "BLK": {
            "name": "BlackRock, Inc.",
            "sector": "Asset Management",
            "market_cap_tier": "large_cap",
            "index_membership": ["SP500"],
            "priority": "medium",
            "trading_priority": 13,
            "liquidity": "high",
            "volatility": "medium",
            "dividend_yield_range": [2.5, 4.0],
            "pe_ratio_range": [15, 25],
            "beta_range": [1.0, 1.4],
            "business_type": "asset_management",
            "regulatory_classification": "Asset Manager",
            "headquarters": "New York, NY",
            "exchange": "NYSE"
        },
        "AMG": {
            "name": "Affiliated Managers Group, Inc.",
            "sector": "Asset Management",
            "market_cap_tier": "mid_cap",
            "index_membership": ["SP500"],
            "priority": "low",
            "trading_priority": 25,
            "liquidity": "medium",
            "volatility": "high",
            "dividend_yield_range": [0.5, 2.0],
            "pe_ratio_range": [8, 18],
            "beta_range": [1.2, 1.8],
            "business_type": "asset_management",
            "regulatory_classification": "Asset Manager",
            "headquarters": "West Palm Beach, FL",
            "exchange": "NYSE"
        }
    }
}

# Trading Symbol Groups for Strategy Implementation
TRADING_GROUPS = {
    "big_four_banks": ["JPM", "BAC", "WFC", "C"],  # Largest US banks
    "money_center_banks": ["JPM", "BAC", "WFC", "C"],  # Same as big four
    "investment_banks": ["GS", "MS"],  # Pure investment banks
    "regional_banks": ["USB", "PNC", "TFC", "COF"],  # Major regional banks
    "broker_dealers": ["SCHW", "GS", "MS"],  # Brokerage focus
    "asset_managers": ["BLK", "AMG"],  # Asset management
    "insurance": ["BRK.B", "AIG"],  # Insurance companies
    
    # Priority groupings
    "primary_focus": ["JPM", "BAC", "WFC", "C", "GS"],  # Top 5 priority
    "secondary_focus": ["MS", "USB", "PNC", "SCHW"],  # Secondary priority
    "diversification": ["BLK", "TFC", "COF", "BRK.B"],  # Diversification plays
    
    # Complete financial sector
    "financial_sector_complete": [
        "JPM", "BAC", "WFC", "C", "GS", "MS", "USB", "PNC", 
        "TFC", "COF", "SCHW", "BLK", "BRK.B", "AIG", "AMG"
    ]
}

# Symbol Configuration by Trading Priority
SYMBOL_PRIORITIES = {
    1: ["JPM"],         # Highest priority - largest US bank
    2: ["BAC"],         # Second largest bank
    3: ["WFC"],         # Third largest (with regulatory issues)
    4: ["C"],           # Global bank with higher volatility
    5: ["GS"],          # Premier investment bank
    6: ["MS"],          # Major investment bank
    8: ["USB"],         # Best-in-class regional
    9: ["PNC"],         # Strong regional bank
    10: ["SCHW"],       # Brokerage/wealth management
    11: ["TFC"],        # Regional bank (BB&T + SunTrust merger)
    12: ["COF"],        # Consumer finance focus
    13: ["BLK"],        # Asset management leader
    15: ["BRK.B"],      # Berkshire Hathaway
    20: ["AIG"],        # Insurance (regulatory history)
    25: ["AMG"]         # Smaller asset manager
}

# Sector Classifications
SECTOR_MAPPING = {
    "Money Center Banks": ["JPM", "BAC", "WFC", "C"],
    "Investment Banking": ["GS", "MS"],
    "Regional Banks": ["USB", "PNC", "TFC"],
    "Consumer Finance": ["COF"],
    "Brokerage": ["SCHW"],
    "Asset Management": ["BLK", "AMG"],
    "Insurance": ["BRK.B", "AIG"]
}

# Market Cap Tiers
MARKET_CAP_TIERS = {
    "mega_cap": {
        "symbols": ["JPM", "BAC", "BRK.B"],
        "min_market_cap": 100_000_000_000,  # $100B USD
        "liquidity": "very_high",
        "volatility": "medium"
    },
    "large_cap": {
        "symbols": ["WFC", "C", "GS", "MS", "USB", "PNC", "TFC", "COF", "SCHW", "BLK", "AIG"],
        "min_market_cap": 10_000_000_000,  # $10B USD
        "liquidity": "high",
        "volatility": "medium"
    },
    "mid_cap": {
        "symbols": ["AMG"],
        "min_market_cap": 2_000_000_000,  # $2B USD
        "liquidity": "medium",
        "volatility": "medium-high"
    }
}

# Trading Session Information for US Markets
TRADING_SESSIONS = {
    "pre_market": {
        "start": "04:00",
        "end": "09:30",
        "timezone": "America/New_York",
        "liquidity": "low",
        "spread": "wide"
    },
    "regular": {
        "start": "09:30",
        "end": "16:00",
        "timezone": "America/New_York",
        "liquidity": "very_high",
        "spread": "tight"
    },
    "after_hours": {
        "start": "16:00",
        "end": "20:00",
        "timezone": "America/New_York",
        "liquidity": "low",
        "spread": "wide"
    }
}

# Symbol-Specific Trading Rules
TRADING_RULES = {
    "JPM": {
        "min_volume_threshold": 5_000_000,  # High liquidity requirement
        "max_position_size": 0.30,  # 30% of portfolio
        "stop_loss_percentage": 0.05,  # 5%
        "take_profit_percentage": 0.10,  # 10%
        "risk_rating": "low",
        "earnings_blackout_days": 2
    },
    "BAC": {
        "min_volume_threshold": 8_000_000,  # Very high volume stock
        "max_position_size": 0.25,
        "stop_loss_percentage": 0.05,
        "take_profit_percentage": 0.10,
        "risk_rating": "low",
        "earnings_blackout_days": 2
    },
    "WFC": {
        "min_volume_threshold": 6_000_000,
        "max_position_size": 0.20,  # Lower due to regulatory risks
        "stop_loss_percentage": 0.06,  # Wider stop due to volatility
        "take_profit_percentage": 0.12,
        "risk_rating": "medium",
        "regulatory_risk": "high",
        "earnings_blackout_days": 3
    },
    "C": {
        "min_volume_threshold": 4_000_000,
        "max_position_size": 0.20,
        "stop_loss_percentage": 0.07,  # Higher volatility
        "take_profit_percentage": 0.15,
        "risk_rating": "medium-high",
        "earnings_blackout_days": 3
    },
    "GS": {
        "min_volume_threshold": 2_000_000,
        "max_position_size": 0.15,  # Higher volatility
        "stop_loss_percentage": 0.08,
        "take_profit_percentage": 0.15,
        "risk_rating": "high",
        "earnings_blackout_days": 3
    }
}

# Regulatory Classifications
REGULATORY_CLASSIFICATIONS = {
    "G-SIB": {
        "description": "Global Systemically Important Banks",
        "symbols": ["JPM", "BAC", "WFC", "C", "GS", "MS"],
        "additional_regulation": "Enhanced capital requirements, stress tests",
        "fed_supervision": True
    },
    "Large Bank": {
        "description": "Banks with >$50B in assets",
        "symbols": ["USB", "PNC", "TFC", "COF", "SCHW"],
        "stress_testing": True,
        "fed_supervision": True
    },
    "Asset Manager": {
        "description": "Asset management companies",
        "symbols": ["BLK", "AMG"],
        "sec_regulation": True,
        "systemic_risk_designation": "Possible"
    }
}

# Data Provider Mappings
DATA_PROVIDER_SYMBOLS = {
    "yahoo_finance": {
        "symbol_suffix": "",  # No suffix for US stocks
        "mapping": {symbol: symbol for symbol in TRADING_GROUPS["financial_sector_complete"]}
    },
    "alpha_vantage": {
        "symbol_suffix": "",
        "mapping": {symbol: symbol for symbol in TRADING_GROUPS["financial_sector_complete"]}
    },
    "marketaux": {
        "symbol_suffix": "",
        "mapping": {symbol: symbol for symbol in TRADING_GROUPS["financial_sector_complete"]}
    },
    "bloomberg": {
        "symbol_suffix": " US Equity",
        "mapping": {symbol: f"{symbol} US Equity" for symbol in TRADING_GROUPS["financial_sector_complete"]}
    }
}

# Economic Sensitivity Analysis
ECONOMIC_SENSITIVITY = {
    "interest_rate_sensitive": {
        "high": ["JPM", "BAC", "WFC", "C", "USB", "PNC", "TFC"],  # Banks benefit from rising rates
        "medium": ["GS", "MS", "COF"],  # Mixed impact
        "low": ["BLK", "SCHW", "BRK.B"]  # Less direct impact
    },
    "credit_cycle_sensitive": {
        "high": ["C", "COF", "WFC"],  # Higher credit risk exposure
        "medium": ["JPM", "BAC", "USB", "PNC", "TFC"],
        "low": ["GS", "MS", "BLK", "SCHW"]  # Fee-based business models
    },
    "market_volatility_sensitive": {
        "high": ["GS", "MS"],  # Trading revenues
        "medium": ["JPM", "BAC", "SCHW"],  # Some trading exposure
        "low": ["USB", "PNC", "TFC", "BLK"]  # Traditional banking/asset mgmt
    }
}

def get_symbols_by_priority(max_priority: int = 10) -> List[str]:
    """Get symbols up to specified priority level"""
    symbols = []
    for priority in sorted(SYMBOL_PRIORITIES.keys()):
        if priority <= max_priority:
            symbols.extend(SYMBOL_PRIORITIES[priority])
    return symbols

def get_symbols_by_sector(sector: str) -> List[str]:
    """Get all symbols for a specific sector"""
    return SECTOR_MAPPING.get(sector, [])

def get_money_center_banks() -> List[str]:
    """Get major US money center banks"""
    return TRADING_GROUPS["big_four_banks"]

def get_investment_banks() -> List[str]:
    """Get pure investment banks"""
    return TRADING_GROUPS["investment_banks"]

def get_primary_trading_symbols() -> List[str]:
    """Get primary symbols for active trading"""
    return TRADING_GROUPS["primary_focus"]

def get_symbol_info(symbol: str) -> Dict[str, Any]:
    """Get comprehensive information for a symbol"""
    # Search through all symbol categories
    all_symbols = {}
    
    for category in FINANCIAL_SECTOR_SYMBOLS.values():
        all_symbols.update(category)
    
    return all_symbols.get(symbol, {})

def get_trading_universe() -> List[str]:
    """Get complete trading universe"""
    return TRADING_GROUPS["financial_sector_complete"]

def validate_symbol(symbol: str) -> bool:
    """Validate if symbol is in our trading universe"""
    return symbol in get_trading_universe()

def get_symbols_for_data_provider(provider: str) -> Dict[str, str]:
    """Get symbol mappings for specific data provider"""
    provider_config = DATA_PROVIDER_SYMBOLS.get(provider, {})
    return provider_config.get("mapping", {})

def get_gsib_banks() -> List[str]:
    """Get Global Systemically Important Banks"""
    return REGULATORY_CLASSIFICATIONS["G-SIB"]["symbols"]

def get_regional_banks() -> List[str]:
    """Get regional banks"""
    return TRADING_GROUPS["regional_banks"]

# Default symbol list for backward compatibility
DEFAULT_SYMBOLS = TRADING_GROUPS["primary_focus"]
