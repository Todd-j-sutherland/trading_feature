#!/usr/bin/env python3
"""
Debug the prediction saving bug - find where 0.5 fallback happens
"""

import sqlite3
import sys
import logging
from datetime import datetime

# Set up logging to see what happens
logging.basicConfig(level=logging.INFO)

sys.path.append('/root/test')

def test_single_prediction():
    """Test a single prediction to debug the fallback issue"""
    
    print("🔬 DEBUGGING PREDICTION SAVING ISSUE")
    print("=" * 50)
    
    try:
        # Import the daily manager which handles morning routine
        from app.services.daily_manager import TradingSystemManager
        
        print("✅ TradingSystemManager imported successfully")
        
        # Create manager
        manager = TradingSystemManager()
        print("✅ Manager created")
        
        # Check current predictions count
        conn = sqlite3.connect('data/trading_predictions.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM predictions WHERE date(prediction_timestamp) = date("now")')
        before_count = cursor.fetchone()[0]
        print(f"📊 Predictions before test: {before_count}")
        conn.close()
        
        # Try to run just the enhanced ML analysis part
        print("\n🧪 Testing enhanced ML analysis...")
        
        try:
            # Import the enhanced analyzer directly
            from enhanced_ml_system.analyzers.enhanced_morning_analyzer_with_ml import EnhancedMorningAnalyzer
            
            analyzer = EnhancedMorningAnalyzer()
            print("✅ Enhanced analyzer created")
            
            # Try to analyze just one symbol
            print("\n🎯 Testing CBA.AX analysis...")
            
            # This is the critical test - let's see what the analyzer produces
            try:
                # Look for analysis methods
                if hasattr(analyzer, 'analyze_symbol'):
                    result = analyzer.analyze_symbol('CBA.AX')
                    print(f"✅ Analysis result: {result}")
                elif hasattr(analyzer, 'run_analysis'):
                    print("🔍 Found run_analysis method")
                    # We need to check the actual method signature
                else:
                    print("🔍 Available methods:")
                    methods = [m for m in dir(analyzer) if not m.startswith('_')]
                    for method in methods[:10]:  # Show first 10
                        print(f"  - {method}")
                        
            except Exception as e:
                print(f"❌ Analysis error: {e}")
                
        except Exception as e:
            print(f"❌ Enhanced analyzer error: {e}")
            import traceback
            traceback.print_exc()
        
        # Check predictions count after
        conn = sqlite3.connect('data/trading_predictions.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM predictions WHERE date(prediction_timestamp) = date("now")')
        after_count = cursor.fetchone()[0]
        print(f"\n📊 Predictions after test: {after_count}")
        
        if after_count > before_count:
            print("🔍 New predictions added - checking values...")
            cursor.execute('SELECT symbol, predicted_action, action_confidence FROM predictions WHERE date(prediction_timestamp) = date("now") ORDER BY prediction_timestamp DESC LIMIT 5')
            new_preds = cursor.fetchall()
            for pred in new_preds:
                conf = pred[2]
                if abs(conf - 0.5) < 0.001:
                    print(f"🚨 {pred[0]}: {pred[1]} conf={conf:.3f} - FALLBACK VALUE!")
                else:
                    print(f"✅ {pred[0]}: {pred[1]} conf={conf:.3f} - Real prediction")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Main error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_single_prediction()
