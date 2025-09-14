"""
USA Financial Markets Regional Configuration

This module provides complete configuration for US financial markets including:
- NYSE, NASDAQ, and other US exchange settings
- Major US banks and financial institutions
- US financial news sources with quality tiers
- ML configuration optimized for US market characteristics

Usage:
    from app.config.regions.usa import USAConfig
    
    config = USAConfig()
    symbols = config.get_primary_symbols()
    news_sources = config.get_news_sources()
"""

import os
import yaml
from typing import Dict, List, Any, Optional
from datetime import datetime, time
import pytz

# Import regional configurations
from .market_config import MARKET_CONFIG, TRADING_HOURS, MARKET_HOLIDAYS, REGULATORY_INFO
from .news_sources import NEWS_SOURCES, TIER_CONFIGURATIONS, REGIONAL_PREFERENCES, PROCESSING_CONFIG
from .symbols import (
    FINANCIAL_SECTOR_SYMBOLS, 
    TRADING_GROUPS, 
    SYMBOL_PRIORITIES,
    TRADING_RULES,
    get_primary_trading_symbols,
    get_money_center_banks,
    get_investment_banks,
    get_symbol_info,
    validate_symbol,
    get_gsib_banks
)

class USAConfig:
    """Complete USA regional configuration manager"""
    
    def __init__(self):
        self.region = "usa"
        self.currency = "USD"
        self.timezone = pytz.timezone("America/New_York")
        self.market_name = "United States Financial Markets"
        
        # Load ML configuration
        self._load_ml_config()
        
    def _load_ml_config(self):
        """Load ML configuration from YAML file"""
        config_path = os.path.join(os.path.dirname(__file__), "ml_config.yaml")
        try:
            with open(config_path, 'r') as f:
                self.ml_config = yaml.safe_load(f)
        except FileNotFoundError:
            # Fallback to basic configuration
            self.ml_config = {
                "models": {"random_forest": {"enabled": True}, "xgboost": {"enabled": True}},
                "training": {"cross_validation": {"n_splits": 6}}
            }
    
    # Market Configuration Methods
    def get_market_config(self) -> Dict[str, Any]:
        """Get complete market configuration"""
        return MARKET_CONFIG
    
    def get_trading_hours(self) -> Dict[str, Any]:
        """Get US trading hours"""
        return TRADING_HOURS
    
    def is_market_open(self, check_time: datetime = None) -> bool:
        """Check if US market is currently open"""
        if check_time is None:
            check_time = datetime.now(self.timezone)
        
        # Check if it's a trading day (Monday-Friday)
        if check_time.weekday() >= 5:  # Weekend
            return False
            
        # Check if it's a market holiday
        date_str = check_time.strftime("%Y-%m-%d")
        if date_str in MARKET_HOLIDAYS.get("2024", []):
            return False
            
        # Check trading hours (9:30 - 16:00 ET)
        market_open = time(9, 30)
        market_close = time(16, 0)
        current_time = check_time.time()
        
        return market_open <= current_time < market_close
    
    def get_current_trading_session(self) -> str:
        """Get current trading session"""
        current_time = datetime.now(self.timezone).time()
        
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
    
    def is_early_close_day(self, check_date: datetime = None) -> bool:
        """Check if given date is an early close day"""
        if check_date is None:
            check_date = datetime.now(self.timezone)
        
        date_str = check_date.strftime("%Y-%m-%d")
        early_close_days = MARKET_HOLIDAYS.get("early_close_days", [])
        return date_str in early_close_days
    
    # Symbol Configuration Methods
    def get_primary_symbols(self) -> List[str]:
        """Get primary trading symbols (Big 4 US banks + Goldman)"""
        return get_primary_trading_symbols()
    
    def get_money_center_banks(self) -> List[str]:
        """Get major US money center banks"""
        return get_money_center_banks()
    
    def get_investment_banks(self) -> List[str]:
        """Get pure investment banks"""
        return get_investment_banks()
    
    def get_gsib_banks(self) -> List[str]:
        """Get Global Systemically Important Banks"""
        return get_gsib_banks()
    
    def get_symbols_by_priority(self, max_priority: int = 10) -> List[str]:
        """Get symbols up to specified priority level"""
        symbols = []
        for priority in sorted(SYMBOL_PRIORITIES.keys()):
            if priority <= max_priority:
                symbols.extend(SYMBOL_PRIORITIES[priority])
        return symbols
    
    def get_symbol_config(self, symbol: str) -> Dict[str, Any]:
        """Get complete configuration for a symbol"""
        symbol_info = get_symbol_info(symbol)
        trading_rules = TRADING_RULES.get(symbol, {})
        
        return {
            **symbol_info,
            "trading_rules": trading_rules,
            "valid": validate_symbol(symbol)
        }
    
    def get_trading_groups(self) -> Dict[str, List[str]]:
        """Get all trading groups"""
        return TRADING_GROUPS
    
    def get_financial_sector_symbols(self) -> List[str]:
        """Get all financial sector symbols"""
        return TRADING_GROUPS["financial_sector_complete"]
    
    # News Configuration Methods
    def get_news_sources(self, tier: Optional[int] = None) -> Dict[str, Any]:
        """Get news sources, optionally filtered by tier"""
        if tier is None:
            return NEWS_SOURCES["rss_feeds"]
        
        return {
            source_id: source_config 
            for source_id, source_config in NEWS_SOURCES["rss_feeds"].items()
            if source_config["tier"] == tier
        }
    
    def get_federal_sources(self) -> Dict[str, Any]:
        """Get tier 1 federal government sources"""
        return self.get_news_sources(tier=1)
    
    def get_premium_financial_sources(self) -> Dict[str, Any]:
        """Get tier 2 premium financial media"""
        return self.get_news_sources(tier=2)
    
    def get_high_priority_news_sources(self) -> Dict[str, Any]:
        """Get tier 1 and tier 2 news sources"""
        high_priority = {}
        for source_id, source_config in NEWS_SOURCES["rss_feeds"].items():
            if source_config["tier"] <= 2:
                high_priority[source_id] = source_config
        return high_priority
    
    def get_news_keywords(self) -> Dict[str, List[str]]:
        """Get news filtering keywords"""
        return NEWS_SOURCES["keywords"]
    
    def get_news_processing_config(self) -> Dict[str, Any]:
        """Get news processing configuration"""
        return PROCESSING_CONFIG
    
    # ML Configuration Methods
    def get_ml_config(self) -> Dict[str, Any]:
        """Get complete ML configuration"""
        return self.ml_config
    
    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """Get configuration for specific ML model"""
        return self.ml_config.get("models", {}).get(model_name, {})
    
    def get_feature_config(self) -> Dict[str, Any]:
        """Get feature engineering configuration"""
        return self.ml_config.get("feature_engineering", {})
    
    def get_training_config(self) -> Dict[str, Any]:
        """Get model training configuration"""
        return self.ml_config.get("training", {})
    
    def get_evaluation_config(self) -> Dict[str, Any]:
        """Get model evaluation configuration"""
        return self.ml_config.get("evaluation", {})
    
    # Regional Settings Methods
    def get_regional_preferences(self) -> Dict[str, Any]:
        """Get regional preferences"""
        return REGIONAL_PREFERENCES
    
    def get_regulatory_info(self) -> Dict[str, Any]:
        """Get regulatory information"""
        return REGULATORY_INFO
    
    def get_currency_info(self) -> Dict[str, Any]:
        """Get currency information"""
        return {
            "currency": self.currency,
            "symbol": "$",
            "decimal_places": 2,
            "is_reserve_currency": True,
            "major_pairs": ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF"],
            "economic_indicators": {
                "central_bank": "Federal Reserve",
                "key_rate": "Federal Funds Rate",
                "inflation_target": "2.0%"
            }
        }
    
    def get_market_characteristics(self) -> Dict[str, Any]:
        """Get US market characteristics"""
        return {
            "high_liquidity": True,
            "high_volatility": True,
            "algorithmic_trading_heavy": True,
            "extended_hours_trading": True,
            "dark_pools": True,
            "circuit_breakers": True,
            "pattern_day_trading_rules": True
        }
    
    # Market Status Methods
    def get_market_status(self) -> Dict[str, Any]:
        """Get comprehensive market status"""
        now = datetime.now(self.timezone)
        
        return {
            "current_time_et": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "trading_session": self.get_current_trading_session(),
            "is_trading_day": now.weekday() < 5,
            "is_holiday": now.strftime("%Y-%m-%d") in MARKET_HOLIDAYS.get("2024", []),
            "is_early_close": self.is_early_close_day(now),
            "market_open": self.is_market_open(now),
            "extended_hours_available": True
        }
    
    # Validation Methods
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate complete regional configuration"""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "summary": {}
        }
        
        # Validate symbols
        primary_symbols = self.get_primary_symbols()
        for symbol in primary_symbols:
            if not validate_symbol(symbol):
                validation_results["errors"].append(f"Invalid primary symbol: {symbol}")
                validation_results["valid"] = False
        
        # Validate news sources
        news_sources = self.get_news_sources()
        if len(news_sources) == 0:
            validation_results["errors"].append("No news sources configured")
            validation_results["valid"] = False
        
        # Validate ML configuration
        if not self.ml_config:
            validation_results["errors"].append("ML configuration not loaded")
            validation_results["valid"] = False
        
        # Check for G-SIB coverage
        gsib_banks = self.get_gsib_banks()
        if len(gsib_banks) < 4:
            validation_results["warnings"].append("Less than 4 G-SIB banks in primary symbols")
        
        # Summary
        validation_results["summary"] = {
            "total_symbols": len(self.get_financial_sector_symbols()),
            "primary_symbols": len(primary_symbols),
            "gsib_banks": len(gsib_banks),
            "news_sources": len(news_sources),
            "federal_sources": len(self.get_federal_sources()),
            "ml_models": len(self.ml_config.get("models", {})),
            "timezone": str(self.timezone),
            "currency": self.currency
        }
        
        return validation_results
    
    # Export Methods
    def export_config(self) -> Dict[str, Any]:
        """Export complete configuration as dictionary"""
        return {
            "region": self.region,
            "market_name": self.market_name,
            "currency": self.currency,
            "timezone": str(self.timezone),
            "market_config": self.get_market_config(),
            "symbols": {
                "primary": self.get_primary_symbols(),
                "money_center_banks": self.get_money_center_banks(),
                "investment_banks": self.get_investment_banks(),
                "gsib_banks": self.get_gsib_banks(),
                "financial_sector": self.get_financial_sector_symbols(),
                "trading_groups": self.get_trading_groups()
            },
            "news_sources": self.get_news_sources(),
            "ml_config": self.get_ml_config(),
            "regional_preferences": self.get_regional_preferences(),
            "regulatory_info": self.get_regulatory_info(),
            "market_status": self.get_market_status()
        }

# Convenience functions for backward compatibility
def get_usa_symbols() -> List[str]:
    """Get primary USA symbols"""
    config = USAConfig()
    return config.get_primary_symbols()

def get_usa_news_sources() -> Dict[str, Any]:
    """Get USA news sources"""
    config = USAConfig()
    return config.get_news_sources()

def get_usa_config() -> USAConfig:
    """Get USA configuration instance"""
    return USAConfig()

def get_money_center_banks() -> List[str]:
    """Get US money center banks"""
    config = USAConfig()
    return config.get_money_center_banks()

def get_gsib_banks() -> List[str]:
    """Get Global Systemically Important Banks"""
    config = USAConfig()
    return config.get_gsib_banks()

# Module exports
__all__ = [
    "USAConfig",
    "get_usa_symbols",
    "get_usa_news_sources",
    "get_usa_config",
    "get_money_center_banks",
    "get_gsib_banks",
    "MARKET_CONFIG",
    "NEWS_SOURCES",
    "FINANCIAL_SECTOR_SYMBOLS",
    "TRADING_GROUPS"
]
