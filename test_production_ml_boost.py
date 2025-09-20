#!/usr/bin/env python3
from production.cron.enhanced_fixed_price_mapping_system import comprehensive_threshold_validation

# Test with ML breakdown
prediction_data = {
    "symbol": "TEST.AX",
    "action": "STRONG_BUY", 
    "confidence": 0.95,
    "breakdown_details": "Tech:0.401 + News:0.220 + Vol:0.180 + Risk:0.000 + ML:0.188 x Market:1.00 = 0.950"
}

features_dict = {
    "volume_trend": 0.38,
    "technical_score": 0.75, 
    "news_sentiment": 0.22,
    "risk_assessment": 0.0
}

print("=== Testing Production System ML Boost ===")
validated_action, validated_confidence, meta = comprehensive_threshold_validation(prediction_data, features_dict)
print(f"Result: {validated_action} with confidence {validated_confidence:.3f}")

# Test without ML
prediction_data_no_ml = {
    "symbol": "TEST2.AX",
    "action": "BUY",
    "confidence": 0.75,
    "breakdown_details": "Tech:0.401 + News:0.220 + Vol:0.180 + Risk:0.000"
}

print("\n=== Testing Without ML ===")
validated_action2, validated_confidence2, meta2 = comprehensive_threshold_validation(prediction_data_no_ml, features_dict)
print(f"Result: {validated_action2} with confidence {validated_confidence2:.3f}")
