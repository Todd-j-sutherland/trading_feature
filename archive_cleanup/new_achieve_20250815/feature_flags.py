#!/usr/bin/env python3
"""
Feature Flag Manager for Trading System
======================================

Manages feature flags to safely develop and test new features individually.
Features can be enabled/disabled via environment variables without code changes.

Usage:
    from feature_flags import FeatureFlags
    
    flags = FeatureFlags()
    
    if flags.is_enabled('CONFIDENCE_CALIBRATION'):
        # Run confidence calibration feature
        pass
    
    if flags.is_enabled('ANOMALY_DETECTION'):
        # Run anomaly detection feature
        pass
"""

import os
from typing import Dict, List, Optional
from pathlib import Path
import logging

class FeatureFlags:
    """
    Feature flag management system for trading dashboard
    """
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize feature flags from environment or .env file
        
        Args:
            env_file: Optional path to .env file (defaults to .env in current directory)
        """
        self.logger = logging.getLogger(__name__)
        
        # Load environment variables from .env file if it exists
        if env_file is None:
            env_file = Path('.env')
        
        if Path(env_file).exists():
            self._load_env_file(env_file)
        
        # Define all available feature flags with descriptions
        self.available_features = {
            # Phase 1: Quick Wins
            'CONFIDENCE_CALIBRATION': 'Dynamic ML confidence adjustment based on market conditions',
            'ANOMALY_DETECTION': 'Real-time market anomaly and breaking news detection',
            'BACKTESTING_ENGINE': 'Comprehensive strategy backtesting and validation',
            
            # Phase 2: Enhanced Analytics
            'MULTI_ASSET_CORRELATION': 'Cross-asset correlation and sector rotation analysis',
            'INTRADAY_PATTERNS': 'Time-based pattern recognition and analysis',
            'ADVANCED_VISUALIZATIONS': 'Enhanced charts and interactive visualizations',
            
            # Phase 3: Advanced ML
            'ENSEMBLE_MODELS': 'Multiple ML model combination and ensemble predictions',
            'POSITION_SIZING': 'Dynamic position sizing based on risk and volatility',
            'LIVE_MARKET_DATA': 'Real-time market data integration and streaming',
            
            # Phase 4: Full Trading System
            'PAPER_TRADING': 'Automated paper trading simulation and validation',
            'RISK_DASHBOARD': 'Advanced portfolio risk management dashboard',
            'OPTIONS_FLOW': 'Options flow analysis and unusual activity detection',
            
            # Additional Features
            'MOBILE_ALERTS': 'SMS, email, and push notification alerts',
            'SENTIMENT_MOMENTUM': 'Sentiment velocity and momentum tracking',
            'NEWS_IMPACT': 'News event impact quantification and analysis',
            'DYNAMIC_STOP_LOSS': 'Intelligent stop-loss placement and optimization',
            
            # Development & Testing
            'DEBUG_MODE': 'Enhanced debugging and development logging',
            'PERFORMANCE_MONITORING': 'System performance monitoring and metrics',
            'A_B_TESTING': 'A/B testing framework for feature comparison'
        }
        
        # Cache enabled features for performance
        self._enabled_cache = {}
        self._refresh_cache()
    
    def _load_env_file(self, env_file: Path) -> None:
        """Load environment variables from .env file"""
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
        except Exception as e:
            self.logger.warning(f"Could not load .env file {env_file}: {e}")
    
    def _refresh_cache(self) -> None:
        """Refresh the enabled features cache"""
        self._enabled_cache = {}
        for feature in self.available_features.keys():
            env_var = f"FEATURE_{feature}"
            value = os.getenv(env_var, 'false').lower()
            self._enabled_cache[feature] = value in ('true', '1', 'yes', 'on', 'enabled')
    
    def is_enabled(self, feature_name: str) -> bool:
        """
        Check if a feature is enabled
        
        Args:
            feature_name: Name of the feature (without FEATURE_ prefix)
            
        Returns:
            True if feature is enabled, False otherwise
        """
        feature_name = feature_name.upper()
        
        if feature_name not in self.available_features:
            self.logger.warning(f"Unknown feature flag: {feature_name}")
            return False
        
        return self._enabled_cache.get(feature_name, False)
    
    def enable_feature(self, feature_name: str) -> None:
        """
        Enable a feature (for testing/development)
        
        Args:
            feature_name: Name of the feature to enable
        """
        feature_name = feature_name.upper()
        if feature_name in self.available_features:
            os.environ[f"FEATURE_{feature_name}"] = 'true'
            self._enabled_cache[feature_name] = True
            self.logger.info(f"Enabled feature: {feature_name}")
    
    def disable_feature(self, feature_name: str) -> None:
        """
        Disable a feature (for testing/development)
        
        Args:
            feature_name: Name of the feature to disable
        """
        feature_name = feature_name.upper()
        if feature_name in self.available_features:
            os.environ[f"FEATURE_{feature_name}"] = 'false'
            self._enabled_cache[feature_name] = False
            self.logger.info(f"Disabled feature: {feature_name}")
    
    def get_enabled_features(self) -> List[str]:
        """
        Get list of currently enabled features
        
        Returns:
            List of enabled feature names
        """
        return [feature for feature, enabled in self._enabled_cache.items() if enabled]
    
    def get_disabled_features(self) -> List[str]:
        """
        Get list of currently disabled features
        
        Returns:
            List of disabled feature names
        """
        return [feature for feature, enabled in self._enabled_cache.items() if not enabled]
    
    def get_feature_status(self) -> Dict[str, Dict]:
        """
        Get comprehensive status of all features
        
        Returns:
            Dictionary with feature status and descriptions
        """
        status = {}
        for feature, description in self.available_features.items():
            status[feature] = {
                'enabled': self._enabled_cache.get(feature, False),
                'description': description,
                'env_var': f"FEATURE_{feature}"
            }
        return status
    
    def print_status(self) -> None:
        """Print current status of all features"""
        print("🚀 TRADING SYSTEM FEATURE FLAGS STATUS")
        print("=" * 60)
        
        enabled_features = self.get_enabled_features()
        disabled_features = self.get_disabled_features()
        
        print(f"✅ Enabled Features ({len(enabled_features)}):")
        for feature in enabled_features:
            print(f"   • {feature}: {self.available_features[feature]}")
        
        print(f"\n❌ Disabled Features ({len(disabled_features)}):")
        for feature in disabled_features:
            print(f"   • {feature}: {self.available_features[feature]}")
        
        print(f"\n📊 Summary: {len(enabled_features)}/{len(self.available_features)} features enabled")
    
    def create_env_template(self, output_file: str = '.env.example') -> None:
        """
        Create an .env template file with all available features
        
        Args:
            output_file: Path to output file
        """
        with open(output_file, 'w') as f:
            f.write("# Trading System Feature Flags\n")
            f.write("# Set to 'true' to enable, 'false' to disable\n")
            f.write("# Copy this file to .env and modify as needed\n\n")
            
            # Group features by phase
            phases = {
                'PHASE 1: Quick Wins': ['CONFIDENCE_CALIBRATION', 'ANOMALY_DETECTION', 'BACKTESTING_ENGINE'],
                'PHASE 2: Enhanced Analytics': ['MULTI_ASSET_CORRELATION', 'INTRADAY_PATTERNS', 'ADVANCED_VISUALIZATIONS'],
                'PHASE 3: Advanced ML': ['ENSEMBLE_MODELS', 'POSITION_SIZING', 'LIVE_MARKET_DATA'],
                'PHASE 4: Full Trading System': ['PAPER_TRADING', 'RISK_DASHBOARD', 'OPTIONS_FLOW'],
                'Additional Features': ['MOBILE_ALERTS', 'SENTIMENT_MOMENTUM', 'NEWS_IMPACT', 'DYNAMIC_STOP_LOSS'],
                'Development & Testing': ['DEBUG_MODE', 'PERFORMANCE_MONITORING', 'A_B_TESTING']
            }
            
            for phase, features in phases.items():
                f.write(f"# === {phase} ===\n")
                for feature in features:
                    if feature in self.available_features:
                        f.write(f"FEATURE_{feature}=false\n")
                f.write("\n")
            
            f.write("# === API Keys (when features are enabled) ===\n")
            f.write("# ALPHA_VANTAGE_API_KEY=your_key_here\n")
            f.write("# YAHOO_FINANCE_API_KEY=your_key_here\n")
            f.write("# SLACK_WEBHOOK_URL=your_webhook_here\n")
            f.write("# DISCORD_WEBHOOK_URL=your_webhook_here\n")
        
        print(f"Created feature flag template: {output_file}")


# Convenience decorator for feature gating
def feature_gate(feature_name: str, flags: Optional[FeatureFlags] = None):
    """
    Decorator to gate functions behind feature flags
    
    Args:
        feature_name: Name of the feature flag
        flags: Optional FeatureFlags instance (creates new one if None)
    
    Usage:
        @feature_gate('CONFIDENCE_CALIBRATION')
        def render_confidence_calibration():
            # This function only runs if CONFIDENCE_CALIBRATION is enabled
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            flag_manager = flags or FeatureFlags()
            if flag_manager.is_enabled(feature_name):
                return func(*args, **kwargs)
            else:
                # Feature is disabled - return None or empty result
                return None
        return wrapper
    return decorator


# Global instance for easy access
_global_flags = None

def get_feature_flags() -> FeatureFlags:
    """Get global feature flags instance"""
    global _global_flags
    if _global_flags is None:
        _global_flags = FeatureFlags()
    return _global_flags


def is_feature_enabled(feature_name: str) -> bool:
    """
    Quick check if a feature is enabled
    
    Args:
        feature_name: Name of the feature
        
    Returns:
        True if enabled, False otherwise
    """
    return get_feature_flags().is_enabled(feature_name)


if __name__ == "__main__":
    # Demo usage
    flags = FeatureFlags()
    flags.print_status()
    
    # Test enabling/disabling features
    print("\n🧪 Testing feature toggle:")
    print(f"Confidence Calibration enabled: {flags.is_enabled('CONFIDENCE_CALIBRATION')}")
    
    flags.enable_feature('CONFIDENCE_CALIBRATION')
    print(f"After enabling: {flags.is_enabled('CONFIDENCE_CALIBRATION')}")
    
    flags.disable_feature('CONFIDENCE_CALIBRATION')
    print(f"After disabling: {flags.is_enabled('CONFIDENCE_CALIBRATION')}")
