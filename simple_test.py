import sys
sys.path.append("/root/test/production/cron")
from fixed_price_mapping_system import comprehensive_threshold_validation
prediction_data = {"symbol": "CBA.AX", "action": "BUY", "confidence": 0.95}
features_dict = {"volume_trend": 25.0, "market_trend_pct": 1.2}
result = comprehensive_threshold_validation(prediction_data, features_dict)
print(f"Input: 95.0%, Output: {result.get(confidence, 0)*100:.1f}%")
if result.get(confidence, 0) == 0.95:
    print("SUCCESS: ML confidence preserved!")
else:
    print("FAIL: Confidence was modified")

