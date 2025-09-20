#!/usr/bin/env python3
"""
Test script to verify confidence preservation works correctly
"""
import sys
sys.path.append("production/cron")

# Import the modified validation function
from enhanced_fixed_price_mapping_system import comprehensive_threshold_validation, fix_action_parsing

def test_ml_confidence_preservation():
    """Test that ML-enhanced confidence is preserved"""
    
    print("🧪 Testing Confidence Preservation")
    print("=" * 50)
    
    # Test case 1: High ML confidence with good volume (should preserve)
    test_prediction_good = {
        "symbol": "CBA.AX",
        "action": "STRONG_BUY", 
        "confidence": 0.950
    }
    
    test_features_good = {
        "volume_trend": 38.1,  # Good volume +38%
        "technical_score": 0.401,
        "news_sentiment": 0.220,
        "risk_score": 0.000,
        "market_trend_pct": -0.53  # Neutral market
    }
    
    action, confidence, meta = comprehensive_threshold_validation(test_prediction_good, test_features_good)
    
    print(f"✅ Test 1 - Good Volume:")
    print(f"   Input:  STRONG_BUY @ 95.0%")
    print(f"   Output: {action} @ {confidence:.1%}")
    print(f"   Expected: Should preserve ~95% confidence")
    print(f"   Result: {'✅ PASSED' if confidence > 0.9 else '❌ FAILED'}")
    print()
    
    # Test case 2: High ML confidence with poor volume (should trigger veto)
    test_prediction_poor = {
        "symbol": "MQG.AX",
        "action": "STRONG_BUY",
        "confidence": 0.950
    }
    
    test_features_poor = {
        "volume_trend": -35.0,  # Poor volume -35%
        "technical_score": 0.433,
        "news_sentiment": 0.220,
        "risk_score": 0.050,
        "market_trend_pct": -0.53
    }
    
    action2, confidence2, meta2 = comprehensive_threshold_validation(test_prediction_poor, test_features_poor)
    
    print(f"✅ Test 2 - Poor Volume:")
    print(f"   Input:  STRONG_BUY @ 95.0% (volume -35%)")
    print(f"   Output: {action2} @ {confidence2:.1%}")
    print(f"   Expected: Should trigger volume veto -> HOLD")
    print(f"   Result: {'✅ PASSED' if action2 == 'HOLD' else '❌ FAILED'}")
    print()
    
    # Test case 3: Market penalty scenario
    test_prediction_market = {
        "symbol": "WBC.AX", 
        "action": "STRONG_BUY",
        "confidence": 0.950
    }
    
    test_features_market = {
        "volume_trend": 56.6,  # Good volume
        "technical_score": 0.435,
        "news_sentiment": 0.220,
        "risk_score": 0.050,
        "market_trend_pct": -3.5  # Bad market trend
    }
    
    action3, confidence3, meta3 = comprehensive_threshold_validation(test_prediction_market, test_features_market)
    
    print(f"✅ Test 3 - Market Penalty:")
    print(f"   Input:  STRONG_BUY @ 95.0% (market -3.5%)")
    print(f"   Output: {action3} @ {confidence3:.1%}")
    print(f"   Expected: Should apply 15% market penalty -> ~80%")
    print(f"   Result: {'✅ PASSED' if 0.75 < confidence3 < 0.85 else '❌ FAILED'}")
    print()
    
    print("🎯 SUMMARY:")
    print(f"   Test 1 (Preserve): {'✅' if confidence > 0.9 else '❌'}")
    print(f"   Test 2 (Volume Veto): {'✅' if action2 == 'HOLD' else '❌'}")  
    print(f"   Test 3 (Market Penalty): {'✅' if 0.75 < confidence3 < 0.85 else '❌'}")

if __name__ == "__main__":
    test_ml_confidence_preservation()