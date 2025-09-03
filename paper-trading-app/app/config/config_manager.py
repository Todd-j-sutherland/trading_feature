"""
Robust Configuration Manager
===========================

Centralized configuration management with:
- Environment variable support
- Configuration validation
- Default fallbacks
- Runtime configuration updates
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Optional YAML support
try:
    import yaml
    HAS_YAML = True
except ImportError:
    yaml = None
    HAS_YAML = False

class ConfigurationManager:
    """Robust configuration management system"""
    
    def __init__(self, config_file: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)
        self.config_file = config_file or Path("config") / "trading_config.yml"
        self.config = {}
        self.defaults = self._get_defaults()
        self._load_configuration()
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Get default configuration values"""
        return {
            'database': {
                'path': 'data/trading_predictions.db',
                'timeout': 30,
                'backup_enabled': True
            },
            'api': {
                'timeout': 10,
                'retry_attempts': 3,
                'rate_limit_delay': 1.0
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/trading.log',
                'max_size': '10MB',
                'backup_count': 5
            },
            'ml': {
                'model_path': 'data/ml_models',
                'confidence_threshold': 0.7,
                'feature_cache_ttl': 3600
            },
            'trading': {
                'symbols': ['CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX'],
                'paper_trading': True,
                'max_position_size': 1000
            },
            'analysis': {
                'sentiment_weight': 0.4,
                'technical_weight': 0.6,
                'lookback_days': 30
            }
        }
    
    def _load_configuration(self):
        """Load configuration from file with fallbacks"""
        # Start with defaults
        self.config = self.defaults.copy()
        
        # Try to load from file
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    if self.config_file.suffix.lower() in ['.yml', '.yaml'] and HAS_YAML:
                        file_config = yaml.safe_load(f) or {}
                    elif self.config_file.suffix.lower() in ['.yml', '.yaml'] and not HAS_YAML:
                        self.logger.warning("YAML configuration file found but PyYAML not installed. Using defaults.")
                        file_config = {}
                    else:
                        file_config = json.load(f)
                
                # Merge configurations (file overrides defaults)
                self._merge_config(self.config, file_config)
                self.logger.info(f"Configuration loaded from {self.config_file}")
                
            except Exception as e:
                self.logger.warning(f"Failed to load config file {self.config_file}: {e}")
                self.logger.info("Using default configuration")
        
        # Override with environment variables
        self._load_env_overrides()
        
        # Validate configuration
        self._validate_configuration()
    
    def _merge_config(self, default_config: Dict, override_config: Dict):
        """Recursively merge configuration dictionaries"""
        for key, value in override_config.items():
            if key in default_config and isinstance(default_config[key], dict) and isinstance(value, dict):
                self._merge_config(default_config[key], value)
            else:
                default_config[key] = value
    
    def _load_env_overrides(self):
        """Load configuration overrides from environment variables"""
        env_mappings = {
            'TRADING_DB_PATH': ['database', 'path'],
            'TRADING_API_TIMEOUT': ['api', 'timeout'],
            'TRADING_LOG_LEVEL': ['logging', 'level'],
            'TRADING_PAPER_MODE': ['trading', 'paper_trading'],
            'TRADING_SYMBOLS': ['trading', 'symbols']
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                try:
                    # Type conversion
                    if env_var.endswith('_TIMEOUT'):
                        env_value = int(env_value)
                    elif env_var.endswith('_PAPER_MODE'):
                        env_value = env_value.lower() in ['true', '1', 'yes']
                    elif env_var.endswith('_SYMBOLS'):
                        env_value = env_value.split(',')
                    
                    # Set the config value
                    config_section = self.config
                    for key in config_path[:-1]:
                        config_section = config_section[key]
                    config_section[config_path[-1]] = env_value
                    
                    self.logger.info(f"Environment override: {env_var}")
                    
                except Exception as e:
                    self.logger.warning(f"Invalid environment variable {env_var}: {e}")
    
    def _validate_configuration(self):
        """Validate configuration values"""
        validations = [
            (lambda: self.config['api']['timeout'] > 0, "API timeout must be positive"),
            (lambda: self.config['api']['retry_attempts'] >= 0, "Retry attempts must be non-negative"),
            (lambda: len(self.config['trading']['symbols']) > 0, "Must have at least one trading symbol"),
            (lambda: self.config['ml']['confidence_threshold'] >= 0 and 
                    self.config['ml']['confidence_threshold'] <= 1, "Confidence threshold must be 0-1")
        ]
        
        for validation, error_msg in validations:
            try:
                if not validation():
                    self.logger.error(f"Configuration validation failed: {error_msg}")
                    raise ValueError(error_msg)
            except Exception as e:
                self.logger.error(f"Configuration validation error: {e}")
    
    def get(self, key_path: str, default=None):
        """
        Get configuration value using dot notation
        
        Example: config.get('database.path')
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value):
        """Set configuration value using dot notation"""
        keys = key_path.split('.')
        config_section = self.config
        
        for key in keys[:-1]:
            if key not in config_section:
                config_section[key] = {}
            config_section = config_section[key]
        
        config_section[keys[-1]] = value
        self.logger.info(f"Configuration updated: {key_path} = {value}")
    
    def save(self):
        """Save current configuration to file"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                if self.config_file.suffix.lower() in ['.yml', '.yaml'] and HAS_YAML:
                    yaml.safe_dump(self.config, f, default_flow_style=False)
                else:
                    # Fall back to JSON if YAML not available
                    json.dump(self.config, f, indent=2)
            
            self.logger.info(f"Configuration saved to {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database-specific configuration"""
        return self.config.get('database', {})
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API-specific configuration"""
        return self.config.get('api', {})
    
    def get_trading_config(self) -> Dict[str, Any]:
        """Get trading-specific configuration"""
        return self.config.get('trading', {})
    
    def is_paper_trading(self) -> bool:
        """Check if paper trading mode is enabled"""
        return self.config.get('trading', {}).get('paper_trading', True)
