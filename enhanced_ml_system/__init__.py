"""
Enhanced ML System Package
Advanced machine learning components for trading system
"""

__version__ = "1.0.0"
__author__ = "Trading System"

# Package imports
try:
    from .analyzers.enhanced_morning_analyzer_with_ml import EnhancedMorningAnalyzer
    from .analyzers.enhanced_evening_analyzer_with_ml import EnhancedEveningAnalyzer
except ImportError:
    # Graceful fallback if analyzers can't be imported
    pass

__all__ = [
    'EnhancedMorningAnalyzer',
    'EnhancedEveningAnalyzer'
]
