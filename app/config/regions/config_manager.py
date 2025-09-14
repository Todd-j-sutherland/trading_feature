"""
Multi-Region Configuration Manager

This service provides a unified interface for accessing configuration across multiple
financial markets (ASX, USA, UK, etc.) with intelligent merging and validation.

Features:
- Dynamic region loading and switching
- Base configuration merging with regional overrides
- Validation and error handling
- Caching for performance
- Extensible architecture for new regions

Usage:
    from app.config.regions.config_manager import ConfigManager
    
    # Initialize with specific region
    config = ConfigManager(region="usa")
    symbols = config.get_symbols()
    news_sources = config.get_news_sources()
    
    # Switch regions dynamically
    config.set_region("asx")
    asx_symbols = config.get_symbols()
"""

import os
import importlib
import yaml
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import logging
from pathlib import Path

# Import base configuration
from .base_config import BaseConfig

class ConfigurationError(Exception):
    """Custom exception for configuration-related errors"""
    pass

class RegionNotFoundError(ConfigurationError):
    """Exception raised when a region is not found"""
    pass

class ConfigManager:
    """Multi-region configuration manager with intelligent merging and caching"""
    
    def __init__(self, region: str = "asx", cache_ttl: int = 3600):
        """
        Initialize configuration manager
        
        Args:
            region: Default region to load ('asx', 'usa', 'uk', etc.)
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
        """
        self.current_region = None
        self.base_config = BaseConfig()
        self.cache_ttl = cache_ttl
        
        # Configuration cache
        self._config_cache = {}
        self._cache_timestamps = {}
        
        # Available regions registry
        self.available_regions = ["asx", "usa", "uk", "eu"]
        self._region_configs = {}
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Discover available regions
        self._discover_regions()
        
        # Set initial region
        self.set_region(region)
    
    def _discover_regions(self):
        """Discover available regional configurations"""
        regions_path = Path(__file__).parent
        
        for item in regions_path.iterdir():
            if item.is_dir() and not item.name.startswith('__'):
                region_name = item.name
                init_file = item / "__init__.py"
                
                if init_file.exists():
                    self._available_regions[region_name] = {
                        "path": str(item),
                        "config_class": None,
                        "loaded": False,
                        "last_loaded": None
                    }
        
        self.logger.info(f"Discovered regions: {list(self._available_regions.keys())}")
    
    def _load_region_config(self, region: str):
        """Load configuration for a specific region"""
        if region not in self._available_regions:
            raise RegionNotFoundError(f"Region '{region}' not found. Available regions: {list(self._available_regions.keys())}")
        
        try:
            # Import region module dynamically
            module_name = f"app.config.regions.{region}"
            region_module = importlib.import_module(module_name)
            
            # Get region config class (e.g., ASXConfig, USAConfig)
            config_class_name = f"{region.upper()}Config"
            if hasattr(region_module, config_class_name):
                config_class = getattr(region_module, config_class_name)
                region_config = config_class()
            else:
                # Fallback: look for generic get_config function
                if hasattr(region_module, f"get_{region}_config"):
                    get_config_func = getattr(region_module, f"get_{region}_config")
                    region_config = get_config_func()
                else:
                    raise ConfigurationError(f"No configuration class or function found for region '{region}'")
            
            # Cache the configuration
            self._region_configs[region] = region_config
            self._available_regions[region]["config_class"] = config_class_name
            self._available_regions[region]["loaded"] = True
            self._available_regions[region]["last_loaded"] = datetime.now()
            
            self.logger.info(f"Successfully loaded configuration for region: {region}")
            return region_config
            
        except ImportError as e:
            raise ConfigurationError(f"Failed to import region '{region}': {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration for region '{region}': {e}")
    
    def set_region(self, region: str):
        """Set the current active region"""
        if region == self.current_region:
            return  # Already set
        
        # Load region configuration if not already loaded
        if region not in self._region_configs:
            self._load_region_config(region)
        
        self.current_region = region
        
        # Clear cache when switching regions
        self._clear_cache()
        
        self.logger.info(f"Switched to region: {region}")
    
    def get_current_region(self) -> str:
        """Get the currently active region"""
        return self.current_region
    
    def get_available_regions(self) -> List[str]:
        """Get list of available regions"""
        return list(self._available_regions.keys())
    
    def _get_current_config(self):
        """Get the current region's configuration object"""
        if not self.current_region:
            raise ConfigurationError("No region set")
        
        if self.current_region not in self._region_configs:
            self._load_region_config(self.current_region)
        
        return self._region_configs[self.current_region]
    
    def _merge_with_base_config(self, regional_config: Dict[str, Any], config_type: str) -> Dict[str, Any]:
        """Merge regional configuration with base configuration"""
        base_config_data = {}
        
        # Get relevant base configuration
        if config_type == "technical_indicators":
            base_config_data = self.base_config.get_technical_indicators()
        elif config_type == "risk_parameters":
            base_config_data = self.base_config.get_risk_parameters()
        elif config_type == "ml_config":
            base_config_data = self.base_config.get_ml_base_config()
        elif config_type == "data_quality":
            base_config_data = self.base_config.get_data_quality_standards()
        
        # Deep merge: regional config overrides base config
        merged_config = self._deep_merge(base_config_data, regional_config)
        return merged_config
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries, with override taking precedence"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _get_cached_or_compute(self, cache_key: str, compute_func):
        """Get cached value or compute and cache it"""
        now = datetime.now()
        
        # Check if we have a cached value that's still valid
        if (cache_key in self._config_cache and 
            cache_key in self._cache_timestamps and
            (now - self._cache_timestamps[cache_key]).seconds < self.cache_ttl):
            return self._config_cache[cache_key]
        
        # Compute new value
        value = compute_func()
        
        # Cache it
        self._config_cache[cache_key] = value
        self._cache_timestamps[cache_key] = now
        
        return value
    
    def _clear_cache(self):
        """Clear configuration cache"""
        self._config_cache.clear()
        self._cache_timestamps.clear()
    
    # Public API Methods
    
    def get_symbols(self, symbol_type: str = "primary") -> List[str]:
        """Get symbols for the current region"""
        cache_key = f"{self.current_region}_symbols_{symbol_type}"
        
        def compute_symbols():
            config = self._get_current_config()
            
            if symbol_type == "primary":
                return config.get_primary_symbols()
            elif symbol_type == "financial":
                return config.get_financial_sector_symbols() if hasattr(config, 'get_financial_sector_symbols') else config.get_financial_symbols()
            elif symbol_type == "all":
                if hasattr(config, 'get_trading_universe'):
                    return config.get_trading_universe()
                else:
                    return config.get_financial_sector_symbols() if hasattr(config, 'get_financial_sector_symbols') else []
            else:
                # Try to get symbols by priority or other methods
                if hasattr(config, 'get_symbols_by_priority'):
                    return config.get_symbols_by_priority(10)  # Default to priority <= 10
                else:
                    return config.get_primary_symbols()
        
        return self._get_cached_or_compute(cache_key, compute_symbols)
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get detailed information about a specific symbol"""
        config = self._get_current_config()
        return config.get_symbol_config(symbol) if hasattr(config, 'get_symbol_config') else config.get_symbol_info(symbol)
    
    def get_news_sources(self, tier: Optional[int] = None, priority: str = "all") -> Dict[str, Any]:
        """Get news sources for the current region"""
        cache_key = f"{self.current_region}_news_{tier}_{priority}"
        
        def compute_news_sources():
            config = self._get_current_config()
            
            if priority == "high" and hasattr(config, 'get_high_priority_news_sources'):
                return config.get_high_priority_news_sources()
            elif tier is not None:
                return config.get_news_sources(tier=tier)
            else:
                return config.get_news_sources()
        
        return self._get_cached_or_compute(cache_key, compute_news_sources)
    
    def get_trading_hours(self) -> Dict[str, Any]:
        """Get trading hours for the current region"""
        cache_key = f"{self.current_region}_trading_hours"
        
        def compute_trading_hours():
            config = self._get_current_config()
            return config.get_trading_hours()
        
        return self._get_cached_or_compute(cache_key, compute_trading_hours)
    
    def is_market_open(self, region: Optional[str] = None) -> bool:
        """Check if market is open for the specified or current region"""
        if region and region != self.current_region:
            # Temporarily switch to check other region
            original_region = self.current_region
            self.set_region(region)
            result = self._get_current_config().is_market_open()
            self.set_region(original_region)
            return result
        else:
            config = self._get_current_config()
            return config.is_market_open()
    
    def get_ml_config(self, merge_with_base: bool = True) -> Dict[str, Any]:
        """Get ML configuration for the current region"""
        cache_key = f"{self.current_region}_ml_config_{merge_with_base}"
        
        def compute_ml_config():
            config = self._get_current_config()
            regional_ml_config = config.get_ml_config()
            
            if merge_with_base:
                return self._merge_with_base_config(regional_ml_config, "ml_config")
            else:
                return regional_ml_config
        
        return self._get_cached_or_compute(cache_key, compute_ml_config)
    
    def get_technical_indicators(self, merge_with_base: bool = True) -> Dict[str, Any]:
        """Get technical indicators configuration"""
        cache_key = f"{self.current_region}_technical_indicators_{merge_with_base}"
        
        def compute_technical_indicators():
            config = self._get_current_config()
            
            # Try to get from ML config first
            ml_config = config.get_ml_config()
            regional_indicators = ml_config.get("feature_engineering", {}).get("technical_indicators", {})
            
            if merge_with_base:
                return self._merge_with_base_config(regional_indicators, "technical_indicators")
            else:
                return regional_indicators
        
        return self._get_cached_or_compute(cache_key, compute_technical_indicators)
    
    def get_market_config(self) -> Dict[str, Any]:
        """Get market configuration for the current region"""
        cache_key = f"{self.current_region}_market_config"
        
        def compute_market_config():
            config = self._get_current_config()
            return config.get_market_config()
        
        return self._get_cached_or_compute(cache_key, compute_market_config)
    
    def get_regulatory_info(self) -> Dict[str, Any]:
        """Get regulatory information for the current region"""
        cache_key = f"{self.current_region}_regulatory_info"
        
        def compute_regulatory_info():
            config = self._get_current_config()
            return config.get_regulatory_info()
        
        return self._get_cached_or_compute(cache_key, compute_regulatory_info)
    
    def validate_symbol(self, symbol: str) -> bool:
        """Validate if a symbol is valid for the current region"""
        config = self._get_current_config()
        if hasattr(config, 'validate_symbol'):
            return config.validate_symbol(symbol)
        else:
            # Fallback: check if symbol is in primary symbols
            primary_symbols = self.get_symbols("primary")
            return symbol in primary_symbols
    
    def get_multi_region_symbols(self, regions: List[str] = None) -> Dict[str, List[str]]:
        """Get symbols for multiple regions"""
        if regions is None:
            regions = self.get_available_regions()
        
        original_region = self.current_region
        multi_region_symbols = {}
        
        for region in regions:
            try:
                self.set_region(region)
                multi_region_symbols[region] = self.get_symbols("primary")
            except Exception as e:
                self.logger.error(f"Failed to get symbols for region {region}: {e}")
                multi_region_symbols[region] = []
        
        # Restore original region
        self.set_region(original_region)
        return multi_region_symbols
    
    def get_market_status_all_regions(self) -> Dict[str, Dict[str, Any]]:
        """Get market status for all available regions"""
        original_region = self.current_region
        all_status = {}
        
        for region in self.get_available_regions():
            try:
                self.set_region(region)
                config = self._get_current_config()
                if hasattr(config, 'get_market_status'):
                    all_status[region] = config.get_market_status()
                else:
                    all_status[region] = {
                        "market_open": config.is_market_open(),
                        "region": region,
                        "error": None
                    }
            except Exception as e:
                all_status[region] = {"error": str(e), "region": region}
        
        # Restore original region
        self.set_region(original_region)
        return all_status
    
    def validate_all_configurations(self) -> Dict[str, Dict[str, Any]]:
        """Validate configurations for all regions"""
        original_region = self.current_region
        validation_results = {}
        
        for region in self.get_available_regions():
            try:
                self.set_region(region)
                config = self._get_current_config()
                if hasattr(config, 'validate_configuration'):
                    validation_results[region] = config.validate_configuration()
                else:
                    validation_results[region] = {
                        "valid": True,
                        "warnings": ["No validation method available"],
                        "summary": {"region": region}
                    }
            except Exception as e:
                validation_results[region] = {
                    "valid": False,
                    "errors": [str(e)],
                    "summary": {"region": region}
                }
        
        # Restore original region
        self.set_region(original_region)
        return validation_results
    
    def export_complete_config(self, region: str = None) -> Dict[str, Any]:
        """Export complete configuration for a region"""
        if region:
            original_region = self.current_region
            self.set_region(region)
        
        try:
            config = self._get_current_config()
            
            if hasattr(config, 'export_config'):
                result = config.export_config()
            else:
                # Build basic export
                result = {
                    "region": self.current_region,
                    "symbols": self.get_symbols("all"),
                    "news_sources": self.get_news_sources(),
                    "trading_hours": self.get_trading_hours(),
                    "ml_config": self.get_ml_config(),
                    "market_config": self.get_market_config()
                }
            
            # Add base configuration
            result["base_config"] = {
                "technical_indicators": self.base_config.get_technical_indicators(),
                "risk_parameters": self.base_config.get_risk_parameters(),
                "data_quality_standards": self.base_config.get_data_quality_standards()
            }
            
            return result
            
        finally:
            if region:
                self.set_region(original_region)
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of the configuration manager state"""
        return {
            "current_region": self.current_region,
            "available_regions": self.get_available_regions(),
            "loaded_regions": list(self._region_configs.keys()),
            "cache_size": len(self._config_cache),
            "cache_ttl": self.cache_ttl,
            "base_config_loaded": self.base_config is not None,
            "region_details": {
                region: {
                    "loaded": info["loaded"],
                    "last_loaded": info["last_loaded"].isoformat() if info["last_loaded"] else None,
                    "config_class": info["config_class"]
                }
                for region, info in self._available_regions.items()
            }
        }

# Global configuration manager instance
_global_config_manager = None

def get_config_manager(region: str = "asx") -> ConfigManager:
    """Get global configuration manager instance"""
    global _global_config_manager
    
    if _global_config_manager is None:
        _global_config_manager = ConfigManager(region)
    
    return _global_config_manager

def set_global_region(region: str):
    """Set the global configuration manager region"""
    config_manager = get_config_manager()
    config_manager.set_region(region)

# Convenience functions for easy access
def get_symbols(region: str = None, symbol_type: str = "primary") -> List[str]:
    """Get symbols for specified or current region"""
    config_manager = get_config_manager()
    if region:
        original_region = config_manager.get_current_region()
        config_manager.set_region(region)
        symbols = config_manager.get_symbols(symbol_type)
        config_manager.set_region(original_region)
        return symbols
    else:
        return config_manager.get_symbols(symbol_type)

def get_news_sources(region: str = None, tier: int = None) -> Dict[str, Any]:
    """Get news sources for specified or current region"""
    config_manager = get_config_manager()
    if region:
        original_region = config_manager.get_current_region()
        config_manager.set_region(region)
        sources = config_manager.get_news_sources(tier=tier)
        config_manager.set_region(original_region)
        return sources
    else:
        return config_manager.get_news_sources(tier=tier)

def is_any_market_open() -> Dict[str, bool]:
    """Check if any market is open across all regions"""
    config_manager = get_config_manager()
    return {
        region: config_manager.is_market_open(region)
        for region in config_manager.get_available_regions()
    }
