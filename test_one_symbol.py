#!/usr/bin/env python3
import sys
sys.path.insert(0, "/root/test")

from enhanced_efficient_system_market_aware import MarketAwarePredictor

try:
    predictor = MarketAwarePredictor()
    result = predictor.make_enhanced_prediction("CBA.AX")
    print("Success!")
    print(result)
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()
