#!/usr/bin/env python3
"""
Test script to verify ML performance metrics are calculated correctly
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from dashboard import fetch_ml_performance_metrics, fetch_current_sentiment_scores, fetch_ml_feature_analysis

def test_performance_metrics():
    """Test that all performance metrics are within reasonable ranges"""
    
    print("🧪 Testing ML Performance Metrics...")
    
    try:
        # Test ML performance metrics
        metrics = fetch_ml_performance_metrics()
        
        print(f"✅ Total Predictions: {metrics['total_predictions']}")
        print(f"✅ Average Confidence: {metrics['avg_confidence']:.1%}")
        print(f"✅ Success Rate: {metrics['success_rate']:.1%}")
        print(f"✅ Completed Trades: {metrics['completed_trades']}")
        print(f"✅ Average Return: {metrics['avg_return']:.2f}%")
        print(f"✅ Best Trade: {metrics['best_trade']:.2f}%")
        print(f"✅ Worst Trade: {metrics['worst_trade']:.2f}%")
        
        # Validate ranges
        assert 0 <= metrics['success_rate'] <= 1, f"Success rate {metrics['success_rate']:.1%} out of range"
        assert 0 <= metrics['avg_confidence'] <= 1, f"Confidence {metrics['avg_confidence']:.1%} out of range"
        assert metrics['total_predictions'] > 0, "No predictions found"
        assert metrics['completed_trades'] >= 0, "Negative completed trades"
        
        print("✅ All ML performance metrics are within expected ranges!")
        
    except Exception as e:
        print(f"❌ ML Performance Metrics Error: {e}")
        return False
    
    try:
        # Test sentiment scores
        sentiment_df = fetch_current_sentiment_scores()
        print(f"✅ Sentiment data fetched for {len(sentiment_df)} banks")
        
        # Test feature analysis
        feature_analysis = fetch_ml_feature_analysis()
        usage_rates = feature_analysis['feature_usage']
        
        print("✅ Feature Usage Rates:")
        for feature, rate in usage_rates.items():
            print(f"   - {feature}: {rate:.1f}%")
            assert 0 <= rate <= 100, f"Feature usage rate {rate}% out of range for {feature}"
        
        print("✅ All feature usage rates are within expected ranges!")
        
    except Exception as e:
        print(f"❌ Feature Analysis Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_performance_metrics()
    print(f"\n{'🎉 All tests passed!' if success else '❌ Tests failed!'}")
    sys.exit(0 if success else 1)
