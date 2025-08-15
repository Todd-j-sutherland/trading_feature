#!/usr/bin/env python3
"""
Test Technical Analysis Integration

Quick test to verify technical analysis integration works properly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_technical_integration():
    """Test the technical analysis integration"""
    
    print("🧪 TESTING TECHNICAL ANALYSIS INTEGRATION")
    print("=" * 50)
    
    try:
        # Test import
        print("📦 Testing import...")
        from technical_analysis_engine import TechnicalAnalysisEngine
        print("✅ Import successful")
        
        # Test initialization
        print("🚀 Testing initialization...")
        engine = TechnicalAnalysisEngine()
        print("✅ Initialization successful")
        
        # Test update_database_technical_scores
        print("📊 Testing update_database_technical_scores...")
        success = engine.update_database_technical_scores()
        print(f"✅ Update result: {success}")
        
        # Test get_technical_summary
        print("📈 Testing get_technical_summary...")
        summary = engine.get_technical_summary()
        print(f"✅ Summary generated: {summary['total_banks_analyzed']} symbols analyzed")
        print(f"   📊 BUY: {summary['signals']['BUY']}, HOLD: {summary['signals']['HOLD']}, SELL: {summary['signals']['SELL']}")
        print(f"   🎯 Average score: {summary['average_technical_score']}")
        
        # Test individual methods
        print("🔍 Testing individual analysis methods...")
        ma = engine.calculate_moving_averages("BHP")
        print(f"✅ Moving averages calculated: {ma}")
        
        rsi = engine.calculate_rsi("BHP")
        print(f"✅ RSI calculated: {rsi}")
        
        signals = engine.get_technical_signals("BHP")
        print(f"✅ Technical signals: {signals['trend_signal']} ({signals['strength']})")
        
        print("\n" + "=" * 50)
        print("🏆 ALL TECHNICAL ANALYSIS TESTS PASSED!")
        print("✅ Ready for integration with evening analyzer")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TECHNICAL ANALYSIS TEST FAILED:")
        print(f"   Error: {e}")
        print("=" * 50)
        return False

if __name__ == "__main__":
    success = test_technical_integration()
    sys.exit(0 if success else 1)
