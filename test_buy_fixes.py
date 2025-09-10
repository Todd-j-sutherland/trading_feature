#!/usr/bin/env python3
"""
Test script to validate BUY prediction fixes
Tests against the problematic patterns identified in database analysis
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_efficient_system_market_aware import EnhancedMarketAwarePredictor

def test_problematic_scenarios():
    """Test the fixed BUY logic against problematic scenarios from database analysis"""
    
    predictor = EnhancedMarketAwarePredictor()
    
    print("🧪 TESTING BUY PREDICTION FIXES")
    print("="*50)
    
    # Scenario 1: Tech score below threshold (39-44) with declining volume (-17% to -50%)
    print("\n🧪 Test 1: Low tech score + declining volume (should be HOLD)")
    test_symbol = "TEST.AX"
    
    # Mock problematic data from database analysis
    tech_data = {
        "rsi": 42.0,  # Below 60 threshold
        "macd_histogram": 0.01,
        "price_vs_sma20": -0.5,
        "tech_score": 44.0,  # Below 60 threshold - this was generating BUY signals
        "market_price": 25.50
    }
    
    news_data = {
        "sentiment_score": 0.02,  # Slightly positive
        "news_confidence": 0.6,
        "news_quality_score": 0.7
    }
    
    volume_data = {
        "volume_trend": -0.35,  # -35% volume decline (extreme)
        "price_volume_correlation": 0.2,
        "volume_quality_score": 0.4
    }
    
    # Test neutral market (where most problematic predictions occurred)
    market_data = {
        "context": "NEUTRAL",
        "trend_pct": -0.2,  # Slight decline
        "confidence_multiplier": 1.0,
        "buy_threshold": 0.70
    }
    
    result = predictor.calculate_confidence(test_symbol, tech_data, news_data, volume_data, market_data)
    
    print(f"Result: {result['action']} (confidence: {result['confidence']:.3f})")
    if result['action'] != 'HOLD':
        print("❌ FAILED: Should be HOLD due to low tech score and extreme volume decline")
    else:
        print("✅ PASSED: Correctly blocked BUY signal")
    
    # Scenario 2: Volume decline -25% with weak market (should be HOLD)
    print("\n🧪 Test 2: Moderate volume decline in weak bearish market")
    
    tech_data["tech_score"] = 65.0  # Above basic threshold
    tech_data["rsi"] = 58.0
    volume_data["volume_trend"] = -0.25  # -25% decline
    market_data["context"] = "WEAK_BEARISH"
    market_data["trend_pct"] = -0.8
    market_data["confidence_multiplier"] = 0.9
    market_data["buy_threshold"] = 0.75
    
    result = predictor.calculate_confidence(test_symbol, tech_data, news_data, volume_data, market_data)
    
    print(f"Result: {result['action']} (confidence: {result['confidence']:.3f})")
    if result['action'] != 'HOLD':
        print("❌ FAILED: Should be HOLD due to moderate volume decline in bearish market")
    else:
        print("✅ PASSED: Correctly blocked BUY signal")
    
    # Scenario 3: Good conditions should still allow BUY
    print("\n🧪 Test 3: Strong fundamentals (should be BUY)")
    
    tech_data["tech_score"] = 72.0  # Strong
    tech_data["rsi"] = 35.0  # Oversold (good buy signal)
    news_data["sentiment_score"] = 0.12  # Strong positive sentiment
    news_data["news_confidence"] = 0.8
    volume_data["volume_trend"] = 0.15  # +15% volume growth
    volume_data["price_volume_correlation"] = 0.8
    market_data["context"] = "BULLISH"
    market_data["trend_pct"] = 1.8
    market_data["confidence_multiplier"] = 1.1
    market_data["buy_threshold"] = 0.65
    
    result = predictor.calculate_confidence(test_symbol, tech_data, news_data, volume_data, market_data)
    
    print(f"Result: {result['action']} (confidence: {result['confidence']:.3f})")
    if result['action'] not in ['BUY', 'STRONG_BUY']:
        print("❌ FAILED: Should be BUY with strong fundamentals")
    else:
        print("✅ PASSED: Correctly identified BUY signal")
    
    # Scenario 4: Edge case - marginal tech score with slight volume decline
    print("\n🧪 Test 4: Edge case - marginal conditions")
    
    tech_data["tech_score"] = 62.0  # Just above threshold
    tech_data["rsi"] = 55.0
    news_data["sentiment_score"] = -0.02  # Slightly negative
    volume_data["volume_trend"] = -0.08  # -8% decline (light)
    market_data["context"] = "NEUTRAL"
    market_data["confidence_multiplier"] = 1.0
    market_data["buy_threshold"] = 0.70
    
    result = predictor.calculate_confidence(test_symbol, tech_data, news_data, volume_data, market_data)
    
    print(f"Result: {result['action']} (confidence: {result['confidence']:.3f})")
    if result['action'] == 'BUY':
        print("⚠️ MARGINAL: BUY signal with marginal conditions - monitor closely")
    else:
        print("✅ CONSERVATIVE: Blocked marginal BUY signal")
    
    print(f"\n🎯 SUMMARY")
    print("Fixed BUY logic should now:")
    print("- Block signals when tech_score < 60 (was generating BUY at 39-44)")
    print("- Block signals with volume decline > 15% (was ignoring -17% to -50%)")
    print("- Apply stricter thresholds in bearish markets")
    print("- Require positive sentiment in challenging conditions")
    print("- Block extreme volume declines (>30%) globally")

if __name__ == "__main__":
    test_problematic_scenarios()