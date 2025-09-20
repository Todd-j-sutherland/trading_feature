#!/usr/bin/env python3
from enhanced_efficient_system_market_aware import MarketAwarePredictor

# Test one symbol to see ML integration
predictor = MarketAwarePredictor()
result = predictor.make_enhanced_prediction("CBA.AX")

print("=== ML Integration Test ===")
print(f"Action: {result["predicted_action"]}")
print(f"Confidence: {result["action_confidence"]:.3f}")
print(f"Breakdown: {result["prediction_details"]["final_score_breakdown"]}")
print(f"ML Direction: {result["prediction_details"]["ml_direction"]}")
print(f"ML Confidence: {result["prediction_details"]["ml_confidence"]:.3f}")
print(f"ML Magnitude: {result["prediction_details"]["ml_magnitude"]:.3f}")

# Test production system ML extraction
print("")
print("=== Testing Production ML Extraction ===")
from production.cron.enhanced_fixed_price_mapping_system import comprehensive_threshold_validation

# Simulate production system call
prediction_data = {
    "symbol": "CBA.AX",
    "action": result["predicted_action"],
    "confidence": result["action_confidence"],
    "breakdown_details": result["prediction_details"]["final_score_breakdown"]
}

features_dict = {
    "volume_trend": 0.38,
    "technical_score": 0.75,
    "news_sentiment": 0.22,
    "risk_assessment": 0.0
}

validated_action, validated_confidence, meta = comprehensive_threshold_validation(prediction_data, features_dict)
print(f"Production Validated Action: {validated_action}")
print(f"Production Validated Confidence: {validated_confidence:.3f}")
print(f"Production Meta: {meta}")
