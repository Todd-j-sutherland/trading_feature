#!/usr/bin/env python3
"""
ML Trading Config - Simple configuration for ML trading features
"""

# Simple trading configurations
TRADING_CONFIGS = {
    'default': {
        'confidence_threshold': 0.7,
        'max_positions': 5,
        'risk_tolerance': 0.02,
        'position_size_multiplier': 1.0,
        'stop_loss_multiplier': 1.0,
        'take_profit_multiplier': 1.0,
        'min_confidence': 0.7
    },
    'conservative': {
        'confidence_threshold': 0.8,
        'max_positions': 3,
        'risk_tolerance': 0.01,
        'position_size_multiplier': 0.5,
        'stop_loss_multiplier': 0.8,
        'take_profit_multiplier': 1.5,
        'min_confidence': 0.8
    },
    'moderate': {
        'confidence_threshold': 0.7,
        'max_positions': 5,
        'risk_tolerance': 0.02,
        'position_size_multiplier': 1.0,
        'stop_loss_multiplier': 1.0,
        'take_profit_multiplier': 2.0,
        'min_confidence': 0.7
    },
    'aggressive': {
        'confidence_threshold': 0.6,
        'max_positions': 8,
        'risk_tolerance': 0.03,
        'position_size_multiplier': 1.5,
        'stop_loss_multiplier': 1.2,
        'take_profit_multiplier': 2.5,
        'min_confidence': 0.6
    }
}

class FeatureEngineer:
    """Simple feature engineer for compatibility"""
    
    def __init__(self):
        pass
    
    def create_features(self, data):
        """Create basic features"""
        return {}

class TradingModelOptimizer:
    """Simple trading model optimizer for compatibility"""
    
    def __init__(self):
        pass
    
    def optimize_model(self, model, data):
        """Optimize model - placeholder"""
        return model
