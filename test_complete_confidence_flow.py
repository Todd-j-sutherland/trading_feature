#!/usr/bin/env python3
"""
Complete test of confidence preservation through entire pipeline
"""
import sys
import sqlite3
import datetime
sys.path.append("production/cron")

from fixed_price_mapping_system import comprehensive_threshold_validation, sector_correlation_check, circuit_breaker_check

def test_complete_confidence_flow():
    """Test the complete pipeline with our fixes"""
    
    print("🧪 COMPLETE CONFIDENCE PRESERVATION TEST")
    print("=" * 60)
    
    # Simulate ML-enhanced prediction data
    test_prediction = {
        "symbol": "CBA.AX",
        "action": "STRONG_BUY", 
        "confidence": 0.950  # Our ML confidence
    }
    
    test_features = {
        "volume_trend": 45.0,  # Good volume
        "technical_score": 0.65,
        "news_sentiment": 0.3,
        "risk_score": 0.0,
        "market_trend_pct": -0.8  # Neutral market
    }
    
    print(f"🎯 INPUT: {test_prediction['action']} @ {test_prediction['confidence']:.1%}")
    print()
    
    # Step 1: Individual validation
    print("📋 Step 1: Individual Threshold Validation")
    action1, conf1, meta1 = comprehensive_threshold_validation(test_prediction, test_features)
    print(f"   Result: {action1} @ {conf1:.1%}")
    print()
    
    # Step 2: Batch validation (sector correlation)
    print("📋 Step 2: Sector Correlation Check")
    
    # Simulate batch with potential conflict
    predictions_batch = [
        {"symbol": "CBA.AX", "action": action1, "confidence": conf1},
        {"symbol": "WBC.AX", "action": "SELL", "confidence": 0.80},  # Conflict!
        {"symbol": "ANZ.AX", "action": "BUY", "confidence": 0.75}
    ]
    
    batch_after_sector = sector_correlation_check(predictions_batch)
    cba_after_sector = next(p for p in batch_after_sector if p["symbol"] == "CBA.AX")
    print(f"   Result: {cba_after_sector['action']} @ {cba_after_sector['confidence']:.1%}")
    print()
    
    # Step 3: Circuit breaker check
    print("📋 Step 3: Circuit Breaker Check")
    batch_after_circuit = circuit_breaker_check(batch_after_sector)
    cba_final = next(p for p in batch_after_circuit if p["symbol"] == "CBA.AX")
    print(f"   Result: {cba_final['action']} @ {cba_final['confidence']:.1%}")
    print()
    
    # Summary
    print("🎯 PIPELINE SUMMARY:")
    print(f"   Original ML: {test_prediction['confidence']:.1%}")
    print(f"   After Validation: {conf1:.1%}")
    print(f"   After Sector Check: {cba_after_sector['confidence']:.1%}")
    print(f"   Final Result: {cba_final['confidence']:.1%}")
    print()
    
    # Test results
    confidence_preserved = abs(cba_final['confidence'] - test_prediction['confidence']) < 0.05
    print(f"✅ CONFIDENCE PRESERVATION: {'PASSED' if confidence_preserved else 'FAILED'}")
    
    if confidence_preserved:
        print("🎉 SUCCESS: ML confidence properly preserved through entire pipeline!")
    else:
        print("❌ FAILURE: Confidence was degraded somewhere in the pipeline")
        
    return confidence_preserved

if __name__ == "__main__":
    test_complete_confidence_flow()