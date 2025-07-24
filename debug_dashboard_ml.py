#!/usr/bin/env python3
"""
Debug script to test ML pipeline with dashboard-like data
"""

import sys
import os
import logging

# Add the project root to Python path
sys.path.insert(0, '/Users/toddsutherland/Repos/trading_analysis')

from app.core.ml.enhanced_pipeline import EnhancedMLPipeline

def test_dashboard_ml_integration():
    """Test ML pipeline with dashboard-style data"""
    print("🔍 Testing Dashboard ML Integration...")
    print("=" * 50)
    
    # Initialize ML pipeline
    ml_pipeline = EnhancedMLPipeline()
    
    # Sample sentiment data similar to what the dashboard receives
    analysis_data = {
        'symbol': 'CBA.AX',
        'overall_sentiment': 0.047,
        'confidence': 0.61,
        'sentiment_components': {
            'news': 0.036,
            'reddit': 0.0,
            'events': 0.017,
            'volume': 0.0,
            'momentum': 0.0,
            'ml_trading': 0.0
        },
        'news_count': 10,
        'sentiment_scores': {
            'average_sentiment': 0.161,
            'positive_count': 7,
            'negative_count': 0,
            'neutral_count': 3
        },
        'significant_events': {
            'dividend_announcement': False,
            'earnings_report': False,
            'rating_change': True,
            'product_launch': True,
            'partnership_deal': True
        }
    }
    
    # Market data (mock)
    market_data = {
        'price': 100.0,
        'change_percent': 0.0,
        'volume': 1000000,
        'volatility': 0.15
    }
    
    # Test prediction
    print("1️⃣ Testing ML prediction with dashboard data...")
    prediction_result = ml_pipeline.predict(analysis_data, market_data, [])
    
    print(f"📊 Prediction Result: {prediction_result}")
    
    if 'error' in prediction_result:
        print(f"❌ Error: {prediction_result['error']}")
        return False
    else:
        print("✅ ML prediction successful!")
        print(f"🎯 Ensemble Prediction: {prediction_result.get('ensemble_prediction', 'N/A')}")
        print(f"📈 Ensemble Confidence: {prediction_result.get('ensemble_confidence', 'N/A')}")
        print(f"🔢 Feature Count: {prediction_result.get('feature_count', 'N/A')}")
        
        individual_preds = prediction_result.get('individual_predictions', {})
        print("🔍 Individual Model Predictions:")
        for model, pred in individual_preds.items():
            print(f"   {model}: {pred}")
        
        return True

if __name__ == "__main__":
    test_dashboard_ml_integration()
