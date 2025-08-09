#!/usr/bin/env python3
"""
Test script for ML Dashboard Win Rate functionality
"""

import sqlite3
import sys
import os

# Add current directory to path
sys.path.append('.')

def test_win_rate_query():
    """Test the enhanced win rate query"""
    print("🎯 Testing Win Rate Analysis Query")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('data/trading_unified.db')
        cursor = conn.cursor()
        
        query = """
        SELECT 
            optimal_action,
            COUNT(*) as count,
            ROUND(AVG(confidence_score), 3) as avg_confidence,
            ROUND(AVG(return_pct), 3) as avg_return_pct,
            ROUND(SUM(CASE WHEN return_pct > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_rate_pct,
            SUM(CASE WHEN return_pct > 0 THEN 1 ELSE 0 END) as winning_positions,
            SUM(CASE WHEN return_pct <= 0 THEN 1 ELSE 0 END) as losing_positions,
            ROUND(MAX(return_pct), 3) as best_return_pct,
            ROUND(MIN(return_pct), 3) as worst_return_pct
        FROM enhanced_outcomes 
        GROUP BY optimal_action 
        ORDER BY win_rate_pct DESC
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        print("\n📊 Win Rate Results:")
        print("Position | Total | Winners | Win Rate | Avg Return")
        print("-" * 50)
        
        for row in results:
            action, count, confidence, avg_return, win_rate, winners, losers, best, worst = row
            print(f"{action:<8} | {count:<5} | {winners:<7} | {win_rate}%{'':<4} | {avg_return}%")
        
        conn.close()
        print("\n✅ Query successful!")
        return True
        
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return False

def test_dashboard_functionality():
    """Test dashboard key features"""
    print("\n🤖 Testing Dashboard Functionality")
    print("=" * 50)
    
    try:
        # Test database connection
        conn = sqlite3.connect('data/trading_unified.db')
        
        # Test basic queries
        cursor = conn.cursor()
        
        # Test enhanced_features table
        cursor.execute("SELECT COUNT(*) FROM enhanced_features")
        features_count = cursor.fetchone()[0]
        print(f"✅ Enhanced features: {features_count} records")
        
        # Test enhanced_outcomes table
        cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes")
        outcomes_count = cursor.fetchone()[0]
        print(f"✅ Enhanced outcomes: {outcomes_count} records")
        
        # Test join query
        cursor.execute("""
            SELECT COUNT(*) FROM enhanced_features ef
            JOIN enhanced_outcomes eo ON ef.id = eo.feature_id
        """)
        joined_count = cursor.fetchone()[0]
        print(f"✅ Joined records: {joined_count} records")
        
        conn.close()
        print("\n✅ All database tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 ML Dashboard Win Rate Testing")
    print("=" * 60)
    
    success = True
    
    # Test win rate query
    if not test_win_rate_query():
        success = False
    
    # Test dashboard functionality
    if not test_dashboard_functionality():
        success = False
    
    if success:
        print("\n🎉 ALL TESTS PASSED!")
        print("The ML Dashboard is ready with win rate analysis!")
        print("\nTo run the dashboard:")
        print("python3 -m streamlit run ml_dashboard.py")
    else:
        print("\n❌ Some tests failed")

if __name__ == "__main__":
    main()
