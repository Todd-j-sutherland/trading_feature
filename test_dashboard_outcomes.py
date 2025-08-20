#!/usr/bin/env python3
"""
Dashboard Outcomes Test
Quick test to verify outcomes are visible in dashboard queries
"""

import sqlite3
import pandas as pd
from pathlib import Path

def test_dashboard_outcomes():
    """Test the exact queries used by the comprehensive dashboard"""
    
    db_path = "data/trading_predictions.db"
    
    print("🔍 DASHBOARD OUTCOMES TEST")
    print("=" * 50)
    
    try:
        # Test 1: Outcomes table (main outcomes tab)
        print("\n1️⃣ TESTING OUTCOMES TAB QUERY:")
        print("-" * 30)
        
        conn = sqlite3.connect(db_path)
        
        outcomes_query = """
        SELECT 
            outcome_id,
            prediction_id,
            actual_return,
            entry_price,
            exit_price,
            evaluation_timestamp
        FROM outcomes 
        ORDER BY created_at DESC 
        LIMIT 20
        """
        
        outcomes_df = pd.read_sql_query(outcomes_query, conn)
        
        if not outcomes_df.empty:
            print(f"✅ Found {len(outcomes_df)} outcomes")
            print(f"📊 Outcome details:")
            for _, row in outcomes_df.iterrows():
                symbol = row['prediction_id'].split('_')[1] if '_' in row['prediction_id'] else 'Unknown'
                print(f"   - {symbol}: {row['actual_return']:.3f}% return")
                print(f"     Entry: ${row['entry_price']:.2f} → Exit: ${row['exit_price']:.2f}")
            
            # Performance metrics (what dashboard calculates)
            returns = outcomes_df['actual_return'].dropna()
            if len(returns) > 0:
                print(f"\n📈 Performance Metrics:")
                print(f"   Average Return: {returns.mean():.3f}%")
                print(f"   Win Rate: {(returns > 0).mean():.1%}")
                print(f"   Total Trades: {len(returns)}")
        else:
            print("❌ No outcomes found")
        
        # Test 2: Enhanced outcomes table
        print("\n2️⃣ TESTING ENHANCED OUTCOMES TAB QUERY:")
        print("-" * 30)
        
        enhanced_query = """
        SELECT 
            symbol,
            prediction_timestamp,
            optimal_action,
            confidence_score,
            entry_price,
            exit_price_1h,
            exit_price_4h,
            exit_price_1d,
            return_pct
        FROM enhanced_outcomes 
        ORDER BY prediction_timestamp DESC 
        LIMIT 20
        """
        
        enhanced_df = pd.read_sql_query(enhanced_query, conn)
        
        if not enhanced_df.empty:
            print(f"✅ Found {len(enhanced_df)} enhanced outcomes")
            print(f"📊 Enhanced outcome details:")
            for _, row in enhanced_df.iterrows():
                print(f"   - {row['symbol']}: {row['optimal_action']} @ {row['confidence_score']:.3f}")
        else:
            print("❌ No enhanced outcomes found")
        
        conn.close()
        
        # Test 3: Summary
        print("\n3️⃣ SUMMARY:")
        print("-" * 30)
        
        if not outcomes_df.empty:
            print("✅ Dashboard SHOULD show outcomes in the first tab")
            print("✅ Data is available and queries work correctly")
            print("\n💡 If you can't see outcomes in the dashboard:")
            print("   1. Check you're on the 'Outcomes' tab (first tab)")
            print("   2. Try refreshing the browser page")
            print("   3. Check the dashboard URL (should be port 8501)")
            print("   4. Look for any error messages in the dashboard")
        else:
            print("❌ No outcome data available for dashboard")
        
        print(f"\n🌐 Dashboard should be available at:")
        print(f"   http://170.64.199.151:8501")
        
    except Exception as e:
        print(f"❌ Error testing dashboard queries: {e}")
        return False
    
    return not outcomes_df.empty

if __name__ == "__main__":
    test_dashboard_outcomes()
