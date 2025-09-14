#!/usr/bin/env python3
"""
Enhanced Configuration Service
Integrates all configuration files including settings.py and ml_config.yaml
"""
import asyncio
import os
import sys
import yaml
import json
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import importlib.util

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.base_service import BaseService

class EnhancedConfigurationService(BaseService):
    """Enhanced configuration service that loads all config files"""

    def __init__(self):
        super().__init__("enhanced-config")
        self.config_cache = {}
        self.config_sources = {}
        
        # Initialize all configuration sources
        self._load_all_configurations()
        
        # Register configuration methods
        self.register_handler("get_config", self.get_config)
        self.register_handler("get_settings", self.get_settings)
        self.register_handler("get_ml_config", self.get_ml_config)
        self.register_handler("get_news_sources", self.get_news_sources)
        self.register_handler("get_bank_profiles", self.get_bank_profiles)
        self.register_handler("get_technical_indicators", self.get_technical_indicators)
        self.register_handler("get_risk_parameters", self.get_risk_parameters)
        self.register_handler("reload_config", self.reload_config)
        self.register_handler("validate_config", self.validate_config)

    def _load_all_configurations(self):
        """Load all configuration files"""
        # Load settings.py
        self.config_sources['settings.py'] = self._load_settings_py()
        
        # Load ml_config.yaml
        self.config_sources['ml_config.yaml'] = self._load_ml_config_yaml()
        
        # Merge configurations
        self._merge_configurations()
        
        self.logger.info(f"Loaded {len(self.config_sources)} configuration sources")

    def _load_settings_py(self) -> Optional[Dict]:
        """Load settings.py configuration"""
        try:
            # Try multiple potential settings.py locations
            settings_paths = [
                "app/config/settings.py",
                "settings.py", 
                "config/settings.py",
                "../settings.py"
            ]

            for settings_path in settings_paths:
                if os.path.exists(settings_path):
                    spec = importlib.util.spec_from_file_location("settings", settings_path)
                    settings_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(settings_module)
                    
                    # Extract Settings class configuration
                    if hasattr(settings_module, 'Settings'):
                        settings_class = settings_module.Settings
                        config = {}
                        
                        # Extract all class attributes
                        for attr in dir(settings_class):
                            if not attr.startswith('_') and not callable(getattr(settings_class, attr, None)):
                                config[attr] = getattr(settings_class, attr)
                        
                        self.logger.info(f"Loaded settings.py from {settings_path}")
                        return config
                    
            self.logger.warning("Settings.py not found or no Settings class")
            return None

        except Exception as e:
            self.logger.error(f"Error loading settings.py: {e}")
            return None

    def _load_ml_config_yaml(self) -> Optional[Dict]:
        """Load ml_config.yaml configuration"""
        try:
            # Try multiple potential ml_config.yaml locations
            ml_config_paths = [
                "app/config/ml_config.yaml",
                "ml_config.yaml",
                "config/ml_config.yaml",
                "../ml_config.yaml"
            ]

            for config_path in ml_config_paths:
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        config = yaml.safe_load(f)
                    
                    self.logger.info(f"Loaded ml_config.yaml from {config_path}")
                    return config
                    
            self.logger.warning("ml_config.yaml not found")
            return None

        except Exception as e:
            self.logger.error(f"Error loading ml_config.yaml: {e}")
            return None

    def _merge_configurations(self):
        """Merge all configurations into unified config cache"""
        self.config_cache = {}
        
        # Start with settings.py as base
        if self.config_sources.get('settings.py'):
            self.config_cache.update(self.config_sources['settings.py'])
        
        # Add ML config, merging with existing ML_CONFIG if present
        if self.config_sources.get('ml_config.yaml'):
            ml_yaml_config = self.config_sources['ml_config.yaml']
            
            # If settings.py has ML_CONFIG, merge with YAML
            if 'ML_CONFIG' in self.config_cache:
                self.config_cache['ML_CONFIG'] = self._deep_merge(
                    self.config_cache['ML_CONFIG'], 
                    ml_yaml_config
                )
            else:
                self.config_cache['ML_CONFIG'] = ml_yaml_config
        
        # Create enhanced configurations
        self._create_enhanced_configs()

    def _deep_merge(self, dict1: Dict, dict2: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
                
        return result

    def _create_enhanced_configs(self):
        """Create enhanced configuration sections"""
        # Enhanced news sources with quality scoring
        if 'NEWS_SOURCES' in self.config_cache:
            self.config_cache['ENHANCED_NEWS_SOURCES'] = self._enhance_news_sources()
        
        # Enhanced bank profiles with technical indicators
        if 'BANK_PROFILES' in self.config_cache:
            self.config_cache['ENHANCED_BANK_PROFILES'] = self._enhance_bank_profiles()
        
        # Enhanced ML configuration with YAML integration
        if 'ML_CONFIG' in self.config_cache:
            self.config_cache['ENHANCED_ML_CONFIG'] = self._enhance_ml_config()

    def _enhance_news_sources(self) -> Dict:
        """Enhance news sources with additional metadata"""
        news_sources = self.config_cache['NEWS_SOURCES']
        enhanced = {
            'sources': news_sources.get('rss_feeds', {}),
            'keywords': news_sources.get('keywords', {}),
            'source_quality_tiers': {
                # Tier 1: Government & Central Bank (Highest Quality)
                'tier_1': ['rba', 'abs', 'treasury', 'apra'],
                # Tier 2: Major Financial Media (High Quality)  
                'tier_2': ['afr_companies', 'afr_markets', 'market_index', 'investing_au', 'business_news'],
                # Tier 3: Major News Outlets (Good Quality)
                'tier_3': ['abc_business', 'smh_business', 'the_age_business', 'news_com_au'],
                # Tier 4: Specialized Financial (Medium Quality)
                'tier_4': ['motley_fool_au', 'investor_daily', 'aba_news', 'finsia']
            },
            'quality_scores': {
                # Tier 1 scores
                'rba': 1.0, 'abs': 1.0, 'treasury': 1.0, 'apra': 1.0,
                # Tier 2 scores
                'afr_companies': 0.9, 'afr_markets': 0.9, 'market_index': 0.8, 
                'investing_au': 0.8, 'business_news': 0.8,
                # Tier 3 scores
                'abc_business': 0.7, 'smh_business': 0.7, 'the_age_business': 0.7, 'news_com_au': 0.6,
                # Tier 4 scores
                'motley_fool_au': 0.6, 'investor_daily': 0.6, 'aba_news': 0.7, 'finsia': 0.6
            },
            'update_frequencies': {
                'tier_1': 60,  # Every hour for government sources
                'tier_2': 30,  # Every 30 minutes for financial media
                'tier_3': 45,  # Every 45 minutes for major news
                'tier_4': 60   # Every hour for specialized sources
            }
        }
        return enhanced

    def _enhance_bank_profiles(self) -> Dict:
        """Enhance bank profiles with additional metadata"""
        bank_profiles = self.config_cache['BANK_PROFILES'].copy()
        
        # Add technical analysis preferences for each bank
        for symbol, profile in bank_profiles.items():
            profile['technical_indicators'] = {
                'primary': ['RSI', 'MACD', 'BB'],  # Primary indicators
                'secondary': ['SMA', 'EMA', 'VOLUME'],  # Secondary indicators
                'risk_indicators': ['ATR', 'VWAP'],  # Risk indicators
                'momentum_indicators': ['STOCH'],  # Momentum indicators
                'volatility_threshold': 0.03,  # 3% daily volatility threshold
                'volume_threshold': 1.5  # 1.5x average volume threshold
            }
            
            # Add prediction model preferences
            profile['ml_preferences'] = {
                'sentiment_weight': 0.4,
                'technical_weight': 0.3,
                'fundamental_weight': 0.2,
                'market_context_weight': 0.1,
                'prediction_horizon_days': 5,
                'confidence_threshold': 0.7
            }
        
        return bank_profiles

    def _enhance_ml_config(self) -> Dict:
        """Enhance ML configuration by merging settings.py and YAML configs"""
        ml_config = self.config_cache['ML_CONFIG'].copy()
        
        # Add enhanced model configurations
        if 'model_settings' in ml_config:
            model_settings = ml_config['model_settings']
            
            # Merge with existing models configuration
            if 'models' in ml_config:
                enhanced_models = ml_config['models'].copy()
                
                # Add model settings from YAML
                for model_type in model_settings.get('models', []):
                    if model_type not in enhanced_models:
                        enhanced_models[model_type] = {'enabled': True}
                
                ml_config['enhanced_models'] = enhanced_models
            
            # Add feature engineering configuration
            if 'features' in model_settings:
                ml_config['feature_engineering'] = model_settings['features']
            
            # Add training configuration
            if 'training' in model_settings:
                if 'training' in ml_config:
                    ml_config['training'] = self._deep_merge(ml_config['training'], model_settings['training'])
                else:
                    ml_config['training'] = model_settings['training']
        
        # Add performance monitoring
        if 'performance_thresholds' in ml_config:
            ml_config['monitoring'] = {
                'performance_thresholds': ml_config['performance_thresholds'],
                'retraining_triggers': {
                    'performance_degradation': 0.1,  # 10% performance drop
                    'data_drift_threshold': 0.05,
                    'max_days_without_retrain': 30
                }
            }
        
        return ml_config

    async def get_config(self, section: str = None):
        """Get configuration section or entire config"""
        if section:
            return self.config_cache.get(section, {})
        return self.config_cache

    async def get_settings(self):
        """Get settings.py configuration"""
        return self.config_sources.get('settings.py', {})

    async def get_ml_config(self):
        """Get enhanced ML configuration"""
        return self.config_cache.get('ENHANCED_ML_CONFIG', {})

    async def get_news_sources(self):
        """Get enhanced news sources configuration"""
        return self.config_cache.get('ENHANCED_NEWS_SOURCES', {})

    async def get_bank_profiles(self):
        """Get enhanced bank profiles"""
        return self.config_cache.get('ENHANCED_BANK_PROFILES', {})

    async def get_technical_indicators(self):
        """Get technical indicators configuration"""
        return self.config_cache.get('TECHNICAL_INDICATORS', {})

    async def get_risk_parameters(self):
        """Get risk parameters configuration"""
        return self.config_cache.get('RISK_PARAMETERS', {})

    async def reload_config(self):
        """Reload all configurations"""
        self.config_cache.clear()
        self.config_sources.clear()
        self._load_all_configurations()
        
        return {
            "status": "reloaded",
            "timestamp": datetime.now().isoformat(),
            "sources_loaded": list(self.config_sources.keys()),
            "config_sections": list(self.config_cache.keys())
        }

    async def validate_config(self):
        """Validate all configurations"""
        validation_results = {
            "timestamp": datetime.now().isoformat(),
            "sources": {},
            "sections": {},
            "issues": [],
            "warnings": []
        }

        # Validate sources
        for source_name, config in self.config_sources.items():
            if config:
                validation_results["sources"][source_name] = {
                    "loaded": True,
                    "sections": len(config) if isinstance(config, dict) else 0
                }
            else:
                validation_results["sources"][source_name] = {"loaded": False}
                validation_results["issues"].append(f"Failed to load {source_name}")

        # Validate critical sections
        critical_sections = [
            'BANK_SYMBOLS', 'NEWS_SOURCES', 'TECHNICAL_INDICATORS', 
            'ML_CONFIG', 'MARKET_HOURS', 'RISK_PARAMETERS'
        ]
        
        for section in critical_sections:
            if section in self.config_cache:
                validation_results["sections"][section] = {"present": True}
            else:
                validation_results["sections"][section] = {"present": False}
                validation_results["warnings"].append(f"Missing critical section: {section}")

        # Validate data consistency
        if 'BANK_SYMBOLS' in self.config_cache and 'BANK_PROFILES' in self.config_cache:
            bank_symbols = self.config_cache['BANK_SYMBOLS']
            bank_profiles = self.config_cache['BANK_PROFILES']
            
            missing_profiles = [symbol for symbol in bank_symbols if symbol not in bank_profiles]
            if missing_profiles:
                validation_results["warnings"].append(f"Missing bank profiles for: {missing_profiles}")

        return validation_results

    async def health_check(self):
        """Enhanced health check with configuration status"""
        base_health = await super().health_check()
        
        config_health = {
            **base_health,
            "config_sources_loaded": len(self.config_sources),
            "config_sections": len(self.config_cache),
            "settings_py_loaded": bool(self.config_sources.get('settings.py')),
            "ml_config_yaml_loaded": bool(self.config_sources.get('ml_config.yaml')),
            "critical_configs_present": all(
                section in self.config_cache 
                for section in ['BANK_SYMBOLS', 'NEWS_SOURCES', 'ML_CONFIG']
            )
        }

        return config_health

async def main():
    service = EnhancedConfigurationService()
    await service.start_server()

if __name__ == "__main__":
    asyncio.run(main())
