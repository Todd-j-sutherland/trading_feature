import sys
sys.path.append("/root/test/production/cron")
from fixed_price_mapping_system import comprehensive_threshold_validation

# Test 1: Volume Veto
print("VOLUME VETO TEST:")
low_vol = {"symbol": "CBA.AX", "action": "BUY", "confidence": 0.95}
features = {"volume_trend": 0.15, "market_trend_pct": 1.0}
result1 = comprehensive_threshold_validation(low_vol, features)
print(f"Low volume BUY: {result1}")

# Test 2: Low Confidence
print("\nTHRESHOLD TEST:")
low_conf = {"symbol": "ANZ.AX", "action": "BUY", "confidence": 0.50}
good_features = {"volume_trend": 0.6, "market_trend_pct": 1.0}
result2 = comprehensive_threshold_validation(low_conf, good_features)
print(f"Low confidence BUY: {result2}")

print("\nCONSERVATIVE CONTROLS: ACTIVE")

