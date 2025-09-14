"""
Multi-Region Trading Configuration Package

This package provides comprehensive configuration management for multiple financial markets
including ASX (Australia), USA, and extensible support for UK, Europe, and Asia.

Key Features:
- Regional market configurations (trading hours, holidays, regulations)
- Market-specific symbol lists and trading rules
- Tiered news source systems for each region
- ML configurations optimized for regional market characteristics
- Unified configuration manager for easy region switching

Usage Examples:

    # Basic usage with configuration manager
    from app.config.regions import get_config_manager
    
    config = get_config_manager(region="usa")
    symbols = config.get_symbols()
    news_sources = config.get_news_sources()
    
    # Switch regions dynamically
    config.set_region("asx")
    asx_symbols = config.get_symbols()
    
    # Direct region access
    from app.config.regions.asx import ASXConfig
    from app.config.regions.usa import USAConfig
    
    asx_config = ASXConfig()
    usa_config = USAConfig()
    
    # Convenience functions
    from app.config.regions import get_symbols, get_news_sources
    
    usa_symbols = get_symbols("usa", "primary")
    asx_news = get_news_sources("asx", tier=1)
    
    # Multi-region operations
    all_markets_open = is_any_market_open()
    all_symbols = config.get_multi_region_symbols()

Available Regions:
- asx: Australian Securities Exchange (ASX) - Focus on Big 4 banks and financial sector
- usa: US Markets (NYSE/NASDAQ) - Focus on major US banks and G-SIBs
- uk: (Future) London Stock Exchange (LSE)
- eu: (Future) European markets (EURONEXT)
- asia: (Future) Asian markets (HKEX, TSE)

Regional Components:
Each region contains:
- market_config.py: Trading hours, holidays, regulatory information
- symbols.py: Market-specific symbols with priority and classification
- news_sources.py: Quality-tiered news sources for the region
- ml_config.yaml: ML parameters optimized for regional characteristics
- __init__.py: Region-specific configuration class and utilities
"""

# Import configuration manager and convenience functions
from .config_manager import (
    ConfigManager,
    get_config_manager,
    set_global_region,
    get_symbols,
    get_news_sources,
    is_any_market_open,
    ConfigurationError,
    RegionNotFoundError
)

# Import base configuration
from .base_config import BaseConfig

# Import regional configurations
try:
    from .asx import ASXConfig, get_asx_config, get_asx_symbols
except ImportError:
    ASXConfig = None
    get_asx_config = None
    get_asx_symbols = None

try:
    from .usa import USAConfig, get_usa_config, get_usa_symbols, get_money_center_banks, get_gsib_banks
except ImportError:
    USAConfig = None
    get_usa_config = None
    get_usa_symbols = None
    get_money_center_banks = None
    get_gsib_banks = None

# Version information
__version__ = "1.0.0"
__author__ = "Trading System"
__description__ = "Multi-region trading configuration management system"

# Available regions registry
AVAILABLE_REGIONS = {
    "asx": {
        "name": "Australian Securities Exchange",
        "description": "Australian financial markets with focus on Big 4 banks",
        "timezone": "Australia/Sydney",
        "currency": "AUD",
        "config_class": "ASXConfig",
        "primary_symbols": ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX"],
        "market_hours": "10:00-16:00 AEST"
    },
    "usa": {
        "name": "United States Financial Markets",
        "description": "US markets (NYSE/NASDAQ) with focus on major banks",
        "timezone": "America/New_York",
        "currency": "USD",
        "config_class": "USAConfig", 
        "primary_symbols": ["JPM", "BAC", "WFC", "C", "GS"],
        "market_hours": "09:30-16:00 EST"
    }
}

# Convenience functions for multi-region operations
def get_all_available_regions() -> dict:
    """Get information about all available regions"""
    return AVAILABLE_REGIONS.copy()

def get_region_info(region: str) -> dict:
    """Get detailed information about a specific region"""
    if region not in AVAILABLE_REGIONS:
        raise RegionNotFoundError(f"Region '{region}' not found")
    return AVAILABLE_REGIONS[region].copy()

def compare_regions(regions: list = None) -> dict:
    """Compare multiple regions side by side"""
    if regions is None:
        regions = list(AVAILABLE_REGIONS.keys())
    
    config_manager = get_config_manager()
    comparison = {}
    
    for region in regions:
        if region not in AVAILABLE_REGIONS:
            continue
            
        try:
            config_manager.set_region(region)
            
            comparison[region] = {
                "info": AVAILABLE_REGIONS[region],
                "symbols_count": len(config_manager.get_symbols("all")),
                "primary_symbols": config_manager.get_symbols("primary"),
                "news_sources_count": len(config_manager.get_news_sources()),
                "market_open": config_manager.is_market_open(),
                "trading_hours": config_manager.get_trading_hours(),
                "currency": AVAILABLE_REGIONS[region]["currency"]
            }
        except Exception as e:
            comparison[region] = {
                "info": AVAILABLE_REGIONS[region],
                "error": str(e)
            }
    
    return comparison

def get_global_market_status() -> dict:
    """Get market status for all regions"""
    config_manager = get_config_manager()
    return config_manager.get_market_status_all_regions()

def validate_all_regions() -> dict:
    """Validate configurations for all regions"""
    config_manager = get_config_manager()
    return config_manager.validate_all_configurations()

def get_next_market_open() -> dict:
    """Get the next market to open across all regions"""
    from datetime import datetime, timedelta
    import pytz
    
    config_manager = get_config_manager()
    next_opens = {}
    
    for region in AVAILABLE_REGIONS.keys():
        try:
            config_manager.set_region(region)
            region_tz = pytz.timezone(AVAILABLE_REGIONS[region]["timezone"])
            now = datetime.now(region_tz)
            
            # Simple calculation - could be enhanced with actual market calendar
            trading_hours = config_manager.get_trading_hours()
            open_time = trading_hours.get("regular_session", {}).get("open", "09:30")
            
            # Parse open time
            hour, minute = map(int, open_time.split(":"))
            
            # Calculate next market open
            next_open = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_open <= now:
                next_open += timedelta(days=1)
            
            # Skip weekends (simple logic)
            while next_open.weekday() >= 5:
                next_open += timedelta(days=1)
            
            next_opens[region] = {
                "next_open": next_open.isoformat(),
                "hours_until_open": (next_open - now).total_seconds() / 3600,
                "timezone": str(region_tz),
                "market_name": AVAILABLE_REGIONS[region]["name"]
            }
            
        except Exception as e:
            next_opens[region] = {"error": str(e)}
    
    # Find the earliest next open
    earliest_region = None
    earliest_time = None
    
    for region, info in next_opens.items():
        if "error" not in info:
            if earliest_time is None or info["hours_until_open"] < earliest_time:
                earliest_time = info["hours_until_open"]
                earliest_region = region
    
    return {
        "next_market": earliest_region,
        "next_market_info": next_opens.get(earliest_region, {}),
        "all_markets": next_opens
    }

# Quick setup functions
def setup_for_asx_trading():
    """Quick setup for ASX trading"""
    config_manager = get_config_manager("asx")
    return {
        "config": config_manager,
        "symbols": config_manager.get_symbols("primary"),
        "news_sources": config_manager.get_news_sources(tier=1),
        "market_open": config_manager.is_market_open(),
        "region": "asx"
    }

def setup_for_usa_trading():
    """Quick setup for USA trading"""
    config_manager = get_config_manager("usa")
    return {
        "config": config_manager,
        "symbols": config_manager.get_symbols("primary"),
        "news_sources": config_manager.get_news_sources(tier=1),
        "market_open": config_manager.is_market_open(),
        "region": "usa"
    }

def setup_multi_region_trading(regions: list = None):
    """Setup for multi-region trading"""
    if regions is None:
        regions = ["asx", "usa"]
    
    config_manager = get_config_manager()
    setup = {
        "config_manager": config_manager,
        "regions": {}
    }
    
    for region in regions:
        config_manager.set_region(region)
        setup["regions"][region] = {
            "symbols": config_manager.get_symbols("primary"),
            "market_open": config_manager.is_market_open(),
            "news_sources_count": len(config_manager.get_news_sources()),
            "currency": AVAILABLE_REGIONS[region]["currency"]
        }
    
    return setup

# Export main components
__all__ = [
    # Core classes
    "ConfigManager",
    "BaseConfig",
    "ASXConfig", 
    "USAConfig",
    
    # Configuration manager functions
    "get_config_manager",
    "set_global_region",
    
    # Convenience functions
    "get_symbols",
    "get_news_sources", 
    "is_any_market_open",
    
    # Regional convenience functions
    "get_asx_config",
    "get_asx_symbols",
    "get_usa_config", 
    "get_usa_symbols",
    "get_money_center_banks",
    "get_gsib_banks",
    
    # Multi-region functions
    "get_all_available_regions",
    "get_region_info",
    "compare_regions",
    "get_global_market_status",
    "validate_all_regions",
    "get_next_market_open",
    
    # Quick setup functions
    "setup_for_asx_trading",
    "setup_for_usa_trading",
    "setup_multi_region_trading",
    
    # Exceptions
    "ConfigurationError",
    "RegionNotFoundError",
    
    # Constants
    "AVAILABLE_REGIONS"
]

# Package metadata
__package_info__ = {
    "name": "trading_config_regions",
    "version": __version__,
    "description": __description__,
    "author": __author__,
    "supported_regions": list(AVAILABLE_REGIONS.keys()),
    "features": [
        "Multi-region configuration management",
        "Dynamic region switching",
        "Intelligent configuration merging",
        "Market-specific optimization",
        "Extensible architecture",
        "Comprehensive validation",
        "Performance caching"
    ]
}
