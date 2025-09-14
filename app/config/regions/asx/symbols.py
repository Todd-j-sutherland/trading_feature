"""
ASX (Australian Securities Exchange) Symbols Configuration

This module contains comprehensive ASX stock symbols organized by sectors and market capitalization.
Focus on ASX 200 companies with emphasis on financial sector as per trading strategy.
"""

from typing import Dict, List, Any
from datetime import datetime

# Primary ASX Financial Sector Symbols (Core Trading Focus)
FINANCIAL_SECTOR_SYMBOLS = {
    # Big 4 Banks (Primary Focus)
    "major_banks": {
        "CBA.AX": {
            "name": "Commonwealth Bank of Australia",
            "sector": "Banking",
            "market_cap_tier": "large",
            "asx_index": ["ASX20", "ASX50", "ASX100", "ASX200"],
            "priority": "high",
            "trading_priority": 1,
            "liquidity": "very_high",
            "volatility": "medium",
            "dividend_yield_range": [3.5, 5.5],
            "pe_ratio_range": [12, 18],
            "beta_range": [0.8, 1.2],
            "business_type": "retail_commercial_banking",
            "regulatory_focus": ["APRA", "ASIC"]
        },
        "ANZ.AX": {
            "name": "Australia and New Zealand Banking Group",
            "sector": "Banking", 
            "market_cap_tier": "large",
            "asx_index": ["ASX20", "ASX50", "ASX100", "ASX200"],
            "priority": "high",
            "trading_priority": 2,
            "liquidity": "very_high",
            "volatility": "medium",
            "dividend_yield_range": [4.0, 6.0],
            "pe_ratio_range": [10, 16],
            "beta_range": [0.9, 1.3],
            "business_type": "retail_commercial_banking",
            "regulatory_focus": ["APRA", "ASIC"]
        },
        "NAB.AX": {
            "name": "National Australia Bank",
            "sector": "Banking",
            "market_cap_tier": "large", 
            "asx_index": ["ASX20", "ASX50", "ASX100", "ASX200"],
            "priority": "high",
            "trading_priority": 3,
            "liquidity": "very_high",
            "volatility": "medium",
            "dividend_yield_range": [4.5, 6.5],
            "pe_ratio_range": [11, 17],
            "beta_range": [0.8, 1.2],
            "business_type": "retail_commercial_banking",
            "regulatory_focus": ["APRA", "ASIC"]
        },
        "WBC.AX": {
            "name": "Westpac Banking Corporation",
            "sector": "Banking",
            "market_cap_tier": "large",
            "asx_index": ["ASX20", "ASX50", "ASX100", "ASX200"],
            "priority": "high", 
            "trading_priority": 4,
            "liquidity": "very_high",
            "volatility": "medium",
            "dividend_yield_range": [4.0, 6.0],
            "pe_ratio_range": [10, 16],
            "beta_range": [0.9, 1.3],
            "business_type": "retail_commercial_banking",
            "regulatory_focus": ["APRA", "ASIC"]
        }
    },
    
    # Investment Banks & Financial Services
    "investment_finance": {
        "MQG.AX": {
            "name": "Macquarie Group Limited",
            "sector": "Investment Banking",
            "market_cap_tier": "large",
            "asx_index": ["ASX20", "ASX50", "ASX100", "ASX200"],
            "priority": "high",
            "trading_priority": 5,
            "liquidity": "high",
            "volatility": "medium-high",
            "dividend_yield_range": [2.5, 4.5],
            "pe_ratio_range": [12, 20],
            "beta_range": [1.0, 1.5],
            "business_type": "investment_banking_asset_management",
            "regulatory_focus": ["APRA", "ASIC"]
        },
        "AMP.AX": {
            "name": "AMP Limited",
            "sector": "Wealth Management",
            "market_cap_tier": "medium",
            "asx_index": ["ASX100", "ASX200"],
            "priority": "medium",
            "trading_priority": 10,
            "liquidity": "medium",
            "volatility": "high",
            "dividend_yield_range": [0.0, 3.0],
            "pe_ratio_range": [8, 25],
            "beta_range": [1.2, 1.8],
            "business_type": "wealth_management_superannuation",
            "regulatory_focus": ["APRA", "ASIC"]
        },
        "BEN.AX": {
            "name": "Bendigo and Adelaide Bank",
            "sector": "Regional Banking",
            "market_cap_tier": "medium",
            "asx_index": ["ASX200"],
            "priority": "medium",
            "trading_priority": 15,
            "liquidity": "medium",
            "volatility": "medium-high",
            "dividend_yield_range": [4.0, 7.0],
            "pe_ratio_range": [8, 15],
            "beta_range": [1.0, 1.4],
            "business_type": "regional_community_banking",
            "regulatory_focus": ["APRA", "ASIC"]
        }
    },
    
    # Insurance Companies
    "insurance": {
        "SUN.AX": {
            "name": "Suncorp Group Limited",
            "sector": "Insurance",
            "market_cap_tier": "large",
            "asx_index": ["ASX50", "ASX100", "ASX200"],
            "priority": "medium",
            "trading_priority": 12,
            "liquidity": "high",
            "volatility": "medium",
            "dividend_yield_range": [3.0, 5.0],
            "pe_ratio_range": [10, 18],
            "beta_range": [0.8, 1.3],
            "business_type": "general_insurance_banking",
            "regulatory_focus": ["APRA", "ASIC"]
        },
        "IAG.AX": {
            "name": "Insurance Australia Group",
            "sector": "General Insurance",
            "market_cap_tier": "large",
            "asx_index": ["ASX50", "ASX100", "ASX200"],
            "priority": "medium",
            "trading_priority": 13,
            "liquidity": "high",
            "volatility": "medium",
            "dividend_yield_range": [2.5, 4.5],
            "pe_ratio_range": [12, 20],
            "beta_range": [0.7, 1.2],
            "business_type": "general_insurance",
            "regulatory_focus": ["APRA", "ASIC"]
        },
        "QBE.AX": {
            "name": "QBE Insurance Group",
            "sector": "General Insurance",
            "market_cap_tier": "large", 
            "asx_index": ["ASX50", "ASX100", "ASX200"],
            "priority": "medium",
            "trading_priority": 14,
            "liquidity": "high",
            "volatility": "medium-high",
            "dividend_yield_range": [1.0, 3.5],
            "pe_ratio_range": [8, 18],
            "beta_range": [0.9, 1.4],
            "business_type": "international_insurance",
            "regulatory_focus": ["APRA", "ASIC"]
        }
    }
}

# Broader ASX Market Context (Secondary Monitoring)
BROADER_MARKET_SYMBOLS = {
    # ASX 20 Non-Financial (Market Context)
    "market_leaders": {
        "BHP.AX": {
            "name": "BHP Group Limited",
            "sector": "Mining",
            "market_cap_tier": "large",
            "asx_index": ["ASX20", "ASX50", "ASX100", "ASX200"],
            "priority": "low",
            "trading_priority": 20,
            "business_type": "diversified_mining"
        },
        "CSL.AX": {
            "name": "CSL Limited", 
            "sector": "Healthcare",
            "market_cap_tier": "large",
            "asx_index": ["ASX20", "ASX50", "ASX100", "ASX200"],
            "priority": "low",
            "trading_priority": 21,
            "business_type": "biotechnology"
        },
        "WOW.AX": {
            "name": "Woolworths Group Limited",
            "sector": "Consumer Staples",
            "market_cap_tier": "large",
            "asx_index": ["ASX20", "ASX50", "ASX100", "ASX200"],
            "priority": "low",
            "trading_priority": 22,
            "business_type": "retail_supermarkets"
        },
        "COL.AX": {
            "name": "Coles Group Limited",
            "sector": "Consumer Staples",
            "market_cap_tier": "large",
            "asx_index": ["ASX50", "ASX100", "ASX200"],
            "priority": "low",
            "trading_priority": 23,
            "business_type": "retail_supermarkets"
        },
        "TLS.AX": {
            "name": "Telstra Corporation Limited",
            "sector": "Telecommunications",
            "market_cap_tier": "large",
            "asx_index": ["ASX20", "ASX50", "ASX100", "ASX200"],
            "priority": "low",
            "trading_priority": 24,
            "business_type": "telecommunications"
        }
    }
}

# Trading Symbol Groups for Strategy Implementation
TRADING_GROUPS = {
    "primary_focus": ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX"],  # Big 4 Banks
    "secondary_focus": ["MQG.AX", "SUN.AX", "IAG.AX"],  # Other Financial
    "market_context": ["BHP.AX", "CSL.AX", "WOW.AX", "COL.AX"],  # Market Leaders
    "high_priority": ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX", "MQG.AX"],
    "financial_sector_complete": [
        "CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX", "MQG.AX", 
        "SUN.AX", "IAG.AX", "QBE.AX", "AMP.AX", "BEN.AX"
    ]
}

# Symbol Configuration by Trading Priority
SYMBOL_PRIORITIES = {
    1: ["CBA.AX"],      # Highest priority
    2: ["ANZ.AX"], 
    3: ["NAB.AX"],
    4: ["WBC.AX"],
    5: ["MQG.AX"],      # Top 5 financial stocks
    10: ["AMP.AX"],     # Medium priority
    12: ["SUN.AX"],
    13: ["IAG.AX"],
    14: ["QBE.AX"],
    15: ["BEN.AX"],     # Secondary financial
    20: ["BHP.AX"],     # Market context only
    21: ["CSL.AX"],
    22: ["WOW.AX"],
    23: ["COL.AX"],
    24: ["TLS.AX"]
}

# Sector Classifications
SECTOR_MAPPING = {
    "Banking": ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX", "BEN.AX"],
    "Investment Banking": ["MQG.AX"],
    "Insurance": ["SUN.AX", "IAG.AX", "QBE.AX"],
    "Wealth Management": ["AMP.AX"],
    "Mining": ["BHP.AX"],
    "Healthcare": ["CSL.AX"], 
    "Consumer Staples": ["WOW.AX", "COL.AX"],
    "Telecommunications": ["TLS.AX"]
}

# Market Cap Tiers
MARKET_CAP_TIERS = {
    "large": {
        "symbols": ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX", "MQG.AX", "BHP.AX", "CSL.AX", "WOW.AX", "COL.AX", "TLS.AX", "SUN.AX", "IAG.AX", "QBE.AX"],
        "min_market_cap": 10_000_000_000,  # $10B AUD
        "liquidity": "high",
        "volatility": "medium"
    },
    "medium": {
        "symbols": ["AMP.AX", "BEN.AX"],
        "min_market_cap": 1_000_000_000,  # $1B AUD
        "liquidity": "medium",
        "volatility": "medium-high"
    }
}

# Trading Session Information
TRADING_SESSIONS = {
    "pre_market": {
        "start": "07:00",
        "end": "10:00",
        "timezone": "Australia/Sydney",
        "liquidity": "low",
        "spread": "wide"
    },
    "regular": {
        "start": "10:00", 
        "end": "16:00",
        "timezone": "Australia/Sydney",
        "liquidity": "high",
        "spread": "normal"
    },
    "post_market": {
        "start": "16:00",
        "end": "17:00", 
        "timezone": "Australia/Sydney",
        "liquidity": "low",
        "spread": "wide"
    }
}

# Symbol-Specific Trading Rules
TRADING_RULES = {
    "CBA.AX": {
        "min_volume_threshold": 1_000_000,  # Minimum daily volume
        "max_position_size": 0.25,  # 25% of portfolio
        "stop_loss_percentage": 0.05,  # 5%
        "take_profit_percentage": 0.10,  # 10%
        "risk_rating": "low"
    },
    "ANZ.AX": {
        "min_volume_threshold": 800_000,
        "max_position_size": 0.25,
        "stop_loss_percentage": 0.05,
        "take_profit_percentage": 0.10,
        "risk_rating": "low"
    },
    "NAB.AX": {
        "min_volume_threshold": 800_000,
        "max_position_size": 0.25,
        "stop_loss_percentage": 0.05,
        "take_profit_percentage": 0.10,
        "risk_rating": "low"
    },
    "WBC.AX": {
        "min_volume_threshold": 800_000,
        "max_position_size": 0.25,
        "stop_loss_percentage": 0.05,
        "take_profit_percentage": 0.10,
        "risk_rating": "low"
    },
    "MQG.AX": {
        "min_volume_threshold": 500_000,
        "max_position_size": 0.20,
        "stop_loss_percentage": 0.06,
        "take_profit_percentage": 0.12,
        "risk_rating": "medium"
    }
}

# Data Provider Mappings
DATA_PROVIDER_SYMBOLS = {
    "yahoo_finance": {
        # Yahoo Finance uses .AX suffix for ASX
        "symbol_suffix": ".AX",
        "mapping": {symbol: symbol for symbol in TRADING_GROUPS["financial_sector_complete"]}
    },
    "alpha_vantage": {
        # Alpha Vantage may not have .AX suffix
        "symbol_suffix": "",
        "mapping": {
            "CBA.AX": "CBA",
            "ANZ.AX": "ANZ", 
            "NAB.AX": "NAB",
            "WBC.AX": "WBC",
            "MQG.AX": "MQG"
        }
    },
    "marketaux": {
        # MarketAux API symbols
        "symbol_suffix": ".AX",
        "mapping": {symbol: symbol for symbol in TRADING_GROUPS["financial_sector_complete"]}
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

def get_financial_sector_symbols() -> List[str]:
    """Get all financial sector symbols"""
    financial_symbols = []
    for sector in ["Banking", "Investment Banking", "Insurance", "Wealth Management"]:
        financial_symbols.extend(SECTOR_MAPPING.get(sector, []))
    return financial_symbols

def get_primary_trading_symbols() -> List[str]:
    """Get primary symbols for active trading"""
    return TRADING_GROUPS["primary_focus"]

def get_symbol_info(symbol: str) -> Dict[str, Any]:
    """Get comprehensive information for a symbol"""
    # Search through all symbol categories
    all_symbols = {}
    
    # Combine all symbol dictionaries
    for category in FINANCIAL_SECTOR_SYMBOLS.values():
        all_symbols.update(category)
    
    for category in BROADER_MARKET_SYMBOLS.values():
        all_symbols.update(category)
    
    return all_symbols.get(symbol, {})

def get_trading_universe() -> List[str]:
    """Get complete trading universe"""
    return TRADING_GROUPS["financial_sector_complete"] + TRADING_GROUPS["market_context"]

def validate_symbol(symbol: str) -> bool:
    """Validate if symbol is in our trading universe"""
    return symbol in get_trading_universe()

def get_symbols_for_data_provider(provider: str) -> Dict[str, str]:
    """Get symbol mappings for specific data provider"""
    provider_config = DATA_PROVIDER_SYMBOLS.get(provider, {})
    return provider_config.get("mapping", {})

# Default symbol list for backward compatibility
DEFAULT_SYMBOLS = TRADING_GROUPS["primary_focus"]
