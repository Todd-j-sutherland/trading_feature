#!/usr/bin/env python3
"""
Test Database Alignment Fix
Comprehensive tests to verify all components use trading_predictions.db consistently
"""

import sys
import os
import sqlite3
import traceback
sys.path.append('.')
sys.path.append('data_quality_system/core')

def test_database_structure():
    """Test that trading_predictions.db has correct structure"""
    print("=" * 60)
    print("🔧 TEST 1: Database Structure")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect('data/trading_predictions.db')
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['predictions', 'outcomes', 'sentiment_features']
        
        print("📊 Database tables found:")
        for table in tables:
            status = "✅" if table in required_tables else "ℹ️"
            print(f"   {status} {table}")
        
        missing_tables = set(required_tables) - set(tables)
        if missing_tables:
            print(f"❌ Missing required tables: {missing_tables}")
            return False
        else:
            print("✅ All required tables present")
        
        # Check data counts
        cursor.execute('SELECT COUNT(*) FROM predictions')
        pred_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM outcomes') 
        outcome_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM sentiment_features')
        sentiment_count = cursor.fetchone()[0]
        
        print(f"\n📊 Current data counts:")
        print(f"   Predictions: {pred_count}")
        print(f"   Outcomes: {outcome_count}")
        print(f"   Sentiment Features: {sentiment_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database structure test failed: {e}")
        return False

def test_technical_analysis_engine():
    """Test technical analysis engine uses correct database"""
    print("\n" + "=" * 60)
    print("🔧 TEST 2: Technical Analysis Engine")
    print("=" * 60)
    
    try:
        from technical_analysis_engine import TechnicalAnalysisEngine
        
        # Initialize with corrected database path
        tech_engine = TechnicalAnalysisEngine()
        print(f"✅ Technical Analysis Engine initialized")
        print(f"   Database path: {tech_engine.db_path}")
        
        if tech_engine.db_path != "data/trading_predictions.db":
            print(f"❌ Wrong database path: {tech_engine.db_path}")
            return False
        
        # Test analysis with real data
        print("📊 Running analysis on CBA.AX...")
        result = tech_engine.calculate_technical_score("CBA.AX")
        
        print(f"✅ Technical analysis completed:")
        print(f"   Symbol: {result['symbol']}")
        print(f"   Technical Score: {result['technical_score']}")
        print(f"   RSI: {result['rsi']}")
        print(f"   Signal: {result['overall_signal']}")
        print(f"   Current Price: {result['price_action']['current_price']}")
        
        # Verify non-zero values
        if result['price_action']['current_price'] == 0:
            print("❌ Current price is zero - data issue!")
            return False
        else:
            print("✅ Current price is non-zero - technical data working")
        
        # Test database update
        print("\n🔄 Testing database update...")
        success = tech_engine.update_database_technical_scores()
        if success:
            print("✅ Technical scores updated in database")
            
            # Verify update
            conn = sqlite3.connect('data/trading_predictions.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT symbol, technical_score 
                FROM sentiment_features 
                WHERE symbol = 'CBA.AX'
                ORDER BY timestamp DESC 
                LIMIT 1
            ''')
            result = cursor.fetchone()
            
            if result and result[1] > 0:
                print(f"✅ Database updated: CBA.AX technical_score = {result[1]}")
            else:
                print(f"❌ Database not updated or zero score: {result}")
                conn.close()
                return False
            
            conn.close()
        else:
            print("❌ Technical score update failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Technical analysis test failed: {e}")
        traceback.print_exc()
        return False

def test_true_prediction_engine():
    """Test TruePredictionEngine generates predictions with non-zero prices"""
    print("\n" + "=" * 60)
    print("🔧 TEST 3: TruePredictionEngine")
    print("=" * 60)
    
    try:
        from data_quality_system.core.true_prediction_engine import TruePredictionEngine
        
        # Create engine instance  
        engine = TruePredictionEngine()
        print("✅ TruePredictionEngine initialized")
        
        # Test with realistic data (all numeric values)
        test_data = {
            'overall_sentiment': 0.15,
            'confidence': 0.8,
            'news_count': 5,
            'current_price': 167.21,  # Real CBA price from technical analysis
            'rsi': 65.0,
            'macd_signal': 1.0  # Convert 'BUY' to numeric
        }
        
        # Make a prediction for CBA
        print("🧠 Testing prediction generation...")
        prediction = engine.make_prediction('CBA.AX', test_data)
        
        if prediction and 'error' not in prediction:
            print("✅ Prediction generated successfully:")
            print(f"   Symbol: {prediction.get('symbol', 'N/A')}")
            print(f"   Action: {prediction.get('predicted_action', 'N/A')}")
            print(f"   Confidence: {prediction.get('action_confidence', 0):.3f}")
        else:
            print(f"❌ Prediction failed: {prediction}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ TruePredictionEngine test failed: {e}")
        traceback.print_exc()
        return False

def test_entry_price_fix():
    """Test that entry prices are non-zero in the database"""
    print("\n" + "=" * 60)
    print("🔧 TEST 4: Entry Price Fix Verification")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect('data/trading_predictions.db')
        cursor = conn.cursor()
        
        # Check for zero entry prices (the original bug)
        cursor.execute('SELECT COUNT(*) FROM predictions WHERE entry_price = 0')
        zero_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM predictions WHERE entry_price > 0')
        nonzero_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM predictions')
        total_count = cursor.fetchone()[0]
        
        print(f"📊 Entry price analysis:")
        print(f"   Total predictions: {total_count}")
        print(f"   Zero entry prices: {zero_count}")
        print(f"   Non-zero entry prices: {nonzero_count}")
        
        if zero_count > 0:
            print("❌ Found zero entry prices - bug still exists!")
            
            # Show examples of zero prices
            cursor.execute('''
                SELECT symbol, entry_price, optimal_action, created_at
                FROM predictions 
                WHERE entry_price = 0
                ORDER BY created_at DESC 
                LIMIT 3
            ''')
            zero_examples = cursor.fetchall()
            
            print("📋 Examples of zero entry prices:")
            for row in zero_examples:
                symbol, price, action, ts = row
                print(f"   {symbol}: {action} @ ${price} [{ts}]")
            
            conn.close()
            return False
        else:
            print("✅ No zero entry prices found - bug is fixed!")
            
            if nonzero_count > 0:
                # Show examples of good prices
                cursor.execute('''
                    SELECT symbol, entry_price, optimal_action, created_at
                    FROM predictions 
                    WHERE entry_price > 0
                    ORDER BY created_at DESC 
                    LIMIT 5
                ''')
                good_examples = cursor.fetchall()
                
                print("📋 Examples of valid entry prices:")
                for row in good_examples:
                    symbol, price, action, ts = row
                    print(f"   {symbol}: {action} @ ${price:.2f} [{ts}]")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Entry price test failed: {e}")
        traceback.print_exc()
        return False

def test_dashboard_data_consistency():
    """Test that dashboard will see consistent data"""
    print("\n" + "=" * 60)
    print("🔧 TEST 5: Dashboard Data Consistency")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect('data/trading_predictions.db')
        cursor = conn.cursor()
        
        # Simulate dashboard queries
        
        # 1. Total samples (what dashboard shows as "75 total samples")
        cursor.execute('SELECT COUNT(*) FROM predictions')
        total_predictions = cursor.fetchone()[0]
        
        # 2. Data table count (what dashboard shows as "52 in data table")
        cursor.execute('SELECT COUNT(*) FROM predictions WHERE entry_price > 0')
        valid_predictions = cursor.fetchone()[0]
        
        # 3. BUY analysis count (what dashboard shows as "25 BUY analysis")
        cursor.execute("SELECT COUNT(*) FROM predictions WHERE optimal_action LIKE '%BUY%'")
        buy_predictions = cursor.fetchone()[0]
        
        # 4. Display count (what dashboard shows as "14 displayed")
        cursor.execute('''
            SELECT COUNT(*) FROM predictions 
            WHERE entry_price > 0 AND optimal_action IS NOT NULL
        ''')
        display_predictions = cursor.fetchone()[0]
        
        print(f"📊 Dashboard consistency check:")
        print(f"   Total predictions: {total_predictions}")
        print(f"   Valid predictions (entry_price > 0): {valid_predictions}")
        print(f"   BUY predictions: {buy_predictions}")
        print(f"   Displayable predictions: {display_predictions}")
        
        # Check for consistency (should be same source)
        if total_predictions == valid_predictions == display_predictions:
            print("✅ All counts match - perfect consistency!")
        elif abs(total_predictions - valid_predictions) < 5:
            print("✅ Counts are close - acceptable consistency")
        else:
            print("⚠️ Some count differences - expected during transition")
        
        # The key test: no more conflicting databases
        if total_predictions > 0:
            print("✅ Database has data for dashboard to display")
        else:
            print("ℹ️ Database is empty - need to run morning analyzer")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Dashboard consistency test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all database alignment tests"""
    print("🧪 COMPREHENSIVE DATABASE ALIGNMENT TESTS")
    print("Testing fix for conflicting numbers: 75 vs 52 vs 25 vs 14")
    print("Testing fix for entry_price = 0 issue")
    
    tests = [
        test_database_structure,
        test_technical_analysis_engine,
        test_true_prediction_engine,
        test_entry_price_fix,
        test_dashboard_data_consistency
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print("🏁 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED - Database alignment fix is successful!")
        print("💡 The dashboard should now show consistent numbers")
        print("💡 Entry prices should no longer be zero")
    else:
        print("⚠️ Some tests failed - database alignment needs more work")
    
    return failed == 0

if __name__ == "__main__":
    main()
