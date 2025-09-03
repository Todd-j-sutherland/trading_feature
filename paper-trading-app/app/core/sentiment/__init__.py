"""Sentiment analysis components"""

# Lazy imports to avoid circular dependencies  
def get_enhanced_scorer():
    from .enhanced_scoring import EnhancedSentimentScorer
    return EnhancedSentimentScorer

def get_temporal_analyzer():
    from .temporal_analyzer import TemporalSentimentAnalyzer
    return TemporalSentimentAnalyzer

def get_integration_manager():
    from .integration import SentimentIntegrationManager
    return SentimentIntegrationManager
