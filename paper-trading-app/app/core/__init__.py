"""Core business logic package"""

# Lazy imports to avoid circular dependencies
def get_sentiment_scorer():
    from .sentiment.enhanced_scoring import EnhancedSentimentScorer
    return EnhancedSentimentScorer

def get_ensemble():
    from .ml.ensemble.enhanced_ensemble import EnhancedTransformerEnsemble
    return EnhancedTransformerEnsemble

def get_training_pipeline():
    from .ml.training.pipeline import MLTrainingPipeline
    return MLTrainingPipeline
