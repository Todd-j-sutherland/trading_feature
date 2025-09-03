"""
Trading Analysis System
A comprehensive trading analysis platform with ML-powered sentiment analysis,
risk assessment, and automated trading signals.
"""

__version__ = "2.0.0"
__author__ = "Trading Analysis Team"
__email__ = "contact@tradinganalysis.com"

# Lazy imports to avoid circular dependencies
def get_settings():
    from .config.settings import Settings
    return Settings

def get_sentiment_scorer():
    from .core.sentiment.enhanced_scoring import EnhancedSentimentScorer
    return EnhancedSentimentScorer

def get_ensemble():
    from .core.ml.ensemble.enhanced_ensemble import EnhancedTransformerEnsemble
    return EnhancedTransformerEnsemble

def get_daily_manager():
    from .services.daily_manager import TradingSystemManager
    return TradingSystemManager
