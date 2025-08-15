#!/usr/bin/env python3
"""
Simple test of enhanced components
"""

import sys
import os
from datetime import datetime

print("Starting simple enhanced test...")

# Test 1: Enhanced ML Pipeline
try:
    print("Testing enhanced ML pipeline...")
    from app.core.ml.enhanced_training_pipeline import EnhancedMLTrainingPipeline
    pipeline = EnhancedMLTrainingPipeline()
    print("✅ Enhanced ML pipeline imported and created")
except Exception as e:
    print(f"❌ Enhanced ML pipeline failed: {e}")

# Test 2: Technical Analyzer
try:
    print("Testing technical analyzer...")
    from app.core.analysis.technical import TechnicalAnalyzer
    from app.config.settings import Settings
    settings = Settings()
    tech_analyzer = TechnicalAnalyzer(settings)
    print("✅ Technical analyzer imported and created")
except Exception as e:
    print(f"❌ Technical analyzer failed: {e}")

# Test 3: News Sentiment Analyzer
try:
    print("Testing news sentiment analyzer...")
    from app.core.sentiment.news_analyzer import NewsSentimentAnalyzer
    news_analyzer = NewsSentimentAnalyzer()
    print("✅ News sentiment analyzer imported and created")
except Exception as e:
    print(f"❌ News sentiment analyzer failed: {e}")

# Test 4: Simple prediction test
try:
    print("Testing simple prediction...")
    features = {
        'sentiment_score': 0.5,
        'confidence': 0.8,
        'rsi': 55.0,
        'macd_line': 0.02,
        'volume_ratio': 1.2,
        'price_change_1d': 0.5
    }
    
    prediction = pipeline.predict_enhanced('CBA.AX', features)
    print(f"✅ Prediction successful: {prediction}")
except Exception as e:
    print(f"❌ Prediction failed: {e}")

print("Test completed!")
