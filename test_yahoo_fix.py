#!/usr/bin/env python3
"""
Test Yahoo Finance Exit Price Fixing - Small Scale Test

This script tests the Yahoo Finance approach on a small sample to validate it works
before running on the full dataset of 168 missing exit prices.
"""

import sqlite3
from datetime import datetime, timedelta

def test_yahoo_approach():
    """Test the Yahoo Finance approach on a small sample"""
    
    print("🧪 TESTING YAHOO FINANCE EXIT PRICE APPROACH")
    print("=" * 50)
    
    # Check if dependencies are installed
    try:
        import yfinance as yf
        import pandas as pd
        print("✅ Dependencies available: yfinance, pandas")
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("\n📦 To install dependencies, run:")
        print("pip install yfinance pandas")
        print("\nOr use the script: python3 fix_exit_prices_with_yahoo.py --install-deps")
        return False
    
    # Test basic Yahoo Finance functionality
    print("\n🔍 Testing Yahoo Finance API...")
    try:
        # Test with CBA.AX (should be reliable)
        ticker = yf.Ticker("CBA.AX")
        hist = ticker.history(period="5d")
        
        if not hist.empty:
            latest_price = hist['Close'].iloc[-1]
            print(f"✅ Yahoo Finance working - CBA.AX latest: ${latest_price:.2f}")
        else:
            print("❌ Yahoo Finance returned empty data")
            return False
            
    except Exception as e:
        print(f"❌ Yahoo Finance test failed: {e}")
        return False
    
    # Test with real data from database
    print("\n📊 Testing with real database samples...")
    
    conn = sqlite3.connect('data/trading_unified.db')
    cursor = conn.cursor()
    
    # Get a few recent outcomes with missing exit prices
    cursor.execute("""
        SELECT id, symbol, prediction_timestamp, entry_price, exit_price_1d
        FROM enhanced_outcomes 
        WHERE exit_price_1d IS NULL 
        AND prediction_timestamp >= date('now', '-7 days')
        LIMIT 3
    """)
    
    test_samples = cursor.fetchall()
    
    if not test_samples:
        print("ℹ️  No recent samples with missing exit prices found")
        # Get any samples for testing
        cursor.execute("""
            SELECT id, symbol, prediction_timestamp, entry_price, exit_price_1d
            FROM enhanced_outcomes 
            WHERE exit_price_1d IS NULL 
            LIMIT 3
        """)
        test_samples = cursor.fetchall()
    
    if not test_samples:
        print("ℹ️  No missing exit prices found - database already complete")
        conn.close()
        return True
    
    print(f"Found {len(test_samples)} samples to test")
    
    successful_tests = 0
    
    for i, (outcome_id, symbol, pred_timestamp, entry_price, exit_price) in enumerate(test_samples):
        print(f"\n🔍 Test {i+1}: Outcome {outcome_id} ({symbol})")
        print(f"   Prediction time: {pred_timestamp}")
        print(f"   Entry price: ${entry_price:.2f}")
        
        try:
            # Calculate 1-day target date
            pred_dt = datetime.fromisoformat(pred_timestamp.replace('Z', '+00:00').replace('+00:00', ''))
            target_date = pred_dt + timedelta(days=1)
            
            print(f"   Target exit date: {target_date.strftime('%Y-%m-%d')}")
            
            # Get historical data
            start_date = target_date - timedelta(days=3)
            end_date = target_date + timedelta(days=3)
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)
            
            if not hist.empty:
                # Try to find closest price
                target_date_only = target_date.date()
                hist.index = hist.index.date
                
                if target_date_only in hist.index:
                    price = float(hist.loc[target_date_only]['Close'])
                    print(f"   ✅ Found exact date price: ${price:.2f}")
                else:
                    available_dates = list(hist.index)
                    closest_date = min(available_dates, key=lambda x: abs((x - target_date_only).days))
                    price = float(hist.loc[closest_date]['Close'])
                    print(f"   ✅ Found closest date ({closest_date}): ${price:.2f}")
                
                # Calculate return
                return_pct = ((price - entry_price) / entry_price) * 100
                print(f"   📊 Calculated return: {return_pct:+.2f}%")
                
                successful_tests += 1
                
            else:
                print(f"   ❌ No historical data found for {symbol}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    conn.close()
    
    print(f"\n📊 TEST RESULTS:")
    print(f"Successful tests: {successful_tests}/{len(test_samples)}")
    print(f"Success rate: {successful_tests/len(test_samples)*100:.1f}%")
    
    if successful_tests > 0:
        print("\n✅ Yahoo Finance approach validated!")
        print("💡 Ready to run full exit price fix")
        return True
    else:
        print("\n❌ Yahoo Finance approach needs debugging")
        return False

def show_missing_data_summary():
    """Show summary of missing data that needs fixing"""
    
    print("\n📊 MISSING DATA ANALYSIS")
    print("=" * 30)
    
    conn = sqlite3.connect('data/trading_unified.db')
    cursor = conn.cursor()
    
    # Total counts
    cursor.execute('SELECT COUNT(*) FROM enhanced_outcomes')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM enhanced_outcomes WHERE exit_price_1d IS NULL')
    missing_1d = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM enhanced_outcomes WHERE exit_price_4h IS NULL')
    missing_4h = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM enhanced_outcomes WHERE exit_price_1h IS NULL')
    missing_1h = cursor.fetchone()[0]
    
    print(f"Total outcomes: {total}")
    print(f"Missing 1-day exit prices: {missing_1d} ({missing_1d/total*100:.1f}%)")
    print(f"Missing 4-hour exit prices: {missing_4h} ({missing_4h/total*100:.1f}%)")
    print(f"Missing 1-hour exit prices: {missing_1h} ({missing_1h/total*100:.1f}%)")
    
    # Show by symbol
    cursor.execute("""
        SELECT symbol, 
               COUNT(*) as total,
               COUNT(CASE WHEN exit_price_1d IS NULL THEN 1 END) as missing_1d
        FROM enhanced_outcomes 
        GROUP BY symbol 
        ORDER BY missing_1d DESC
    """)
    
    print(f"\nMissing data by symbol:")
    print("Symbol     | Total | Missing | %")
    print("-" * 35)
    
    for symbol, total_sym, missing_sym in cursor.fetchall():
        pct = (missing_sym/total_sym*100) if total_sym > 0 else 0
        print(f"{symbol:10} | {total_sym:5} | {missing_sym:7} | {pct:4.1f}%")
    
    conn.close()

if __name__ == '__main__':
    show_missing_data_summary()
    success = test_yahoo_approach()
    
    if success:
        print(f"\n🚀 NEXT STEPS:")
        print("1. Install dependencies: pip install yfinance pandas")
        print("2. Test on small sample: python3 fix_exit_prices_with_yahoo.py --limit 5 --dry-run")
        print("3. Run full fix: python3 fix_exit_prices_with_yahoo.py")
    else:
        print(f"\n🔧 TROUBLESHOOTING NEEDED:")
        print("Check internet connection and Yahoo Finance API access")
