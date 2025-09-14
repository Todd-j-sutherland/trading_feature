"""
ASX (Australian Securities Exchange) Regional Configuration

This module provides complete configuration for Australian financial markets including:
- Market-specific trading rules and hours
- ASX stock symbols and financial sector focus
- Australian news sources with quality tiers
- ML configuration optimized for ASX characteristics

Usage:
    from app.config.regions.asx import ASXConfig
    
    config = ASXConfig()
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
    get_financial_sector_symbols,
    get_symbol_info,
    validate_symbol
)

class ASXConfig:
    """Complete ASX regional configuration manager"""
    
    def __init__(self):
        self.region = "asx"
        self.currency = "AUD"
        self.timezone = pytz.timezone("Australia/Sydney")
        self.market_name = "Australian Securities Exchange"
        
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
                "models": {"random_forest": {"enabled": True}},
                "training": {"cross_validation": {"n_splits": 5}}
            }
    
    # Market Configuration Methods
    def get_market_config(self) -> Dict[str, Any]:
        """Get complete market configuration"""
        return MARKET_CONFIG
    
    def get_trading_hours(self) -> Dict[str, Any]:
        """Get ASX trading hours"""
        return TRADING_HOURS
    
    def is_market_open(self, check_time: datetime = None) -> bool:
        """Check if ASX market is currently open"""
        if check_time is None:
            check_time = datetime.now(self.timezone)
        
        # Check if it's a trading day (Monday-Friday)
        if check_time.weekday() >= 5:  # Weekend
            return False
            
        # Check if it's a market holiday
        date_str = check_time.strftime("%Y-%m-%d")
        if date_str in MARKET_HOLIDAYS.get("2024", []):
            return False
            
        # Check trading hours (10:00 - 16:00 AEST)
        market_open = time(10, 0)
        market_close = time(16, 0)
        current_time = check_time.time()
        
        return market_open <= current_time < market_close
    
    def get_next_trading_day(self, from_date: datetime = None) -> datetime:
        """Get next trading day"""
        if from_date is None:
            from_date = datetime.now(self.timezone)
            
        next_day = from_date
        while True:
            next_day = next_day.replace(hour=10, minute=0, second=0, microsecond=0)
            if self.is_market_open(next_day):
                return next_day
            next_day += timedelta(days=1)
    
    # Symbol Configuration Methods
    def get_primary_symbols(self) -> List[str]:
        """Get primary trading symbols (Big 4 banks)"""
        return get_primary_trading_symbols()
    
    def get_financial_symbols(self) -> List[str]:
        """Get all financial sector symbols"""
        return get_financial_sector_symbols()
    
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
            "major_pairs": ["AUD/USD", "AUD/EUR", "AUD/GBP", "AUD/JPY"],
            "commodity_correlation": True  # AUD is commodity currency
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
        
        # Summary
        validation_results["summary"] = {
            "total_symbols": len(self.get_financial_symbols()),
            "primary_symbols": len(primary_symbols),
            "news_sources": len(news_sources),
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
                "financial_sector": self.get_financial_symbols(),
                "trading_groups": self.get_trading_groups()
            },
            "news_sources": self.get_news_sources(),
            "ml_config": self.get_ml_config(),
            "regional_preferences": self.get_regional_preferences(),
            "regulatory_info": self.get_regulatory_info()
        }

# Convenience functions for backward compatibility
def get_asx_symbols() -> List[str]:
    """Get primary ASX symbols"""
    config = ASXConfig()
    return config.get_primary_symbols()

def get_asx_news_sources() -> Dict[str, Any]:
    """Get ASX news sources"""
    config = ASXConfig()
    return config.get_news_sources()

def get_asx_config() -> ASXConfig:
    """Get ASX configuration instance"""
    return ASXConfig()

# Module exports
__all__ = [
    "ASXConfig",
    "get_asx_symbols",
    "get_asx_news_sources", 
    "get_asx_config",
    "MARKET_CONFIG",
    "NEWS_SOURCES",
    "FINANCIAL_SECTOR_SYMBOLS",
    "TRADING_GROUPS"
]
