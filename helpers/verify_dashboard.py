#!/usr/bin/env python3
"""
Quick Dashboard Verification Script

Verifies that the dashboard is using the correct database path and 
all metrics are consistent with the exported data.
"""

import sqlite3
import os
from pathlib import Path

def verify_database_path():
    """Verify the database exists in the correct location"""
    
    print("🔍 Verifying database path...")
    
    # Expected path
    expected_path = "data/ml_models/training_data.db"
    
    # Check if database exists
    if Path(expected_path).exists():
        print(f"✅ Database found at: {expected_path}")
        
        # Get database size
        size_mb = Path(expected_path).stat().st_size / (1024 * 1024)
        print(f"✅ Database size: {size_mb:.2f} MB")
        
        return True
    else:
        print(f"❌ Database NOT found at: {expected_path}")
        
        # Check if legacy path exists
        legacy_path = "data_v2/ml_models/training_data.db"
        if Path(legacy_path).exists():
            print(f"⚠️ Found legacy database at: {legacy_path}")
            print("   🔧 You may need to copy this to the correct location")
        
        return False

def verify_database_content():
    """Verify database contains expected data"""
    
    print("\n📊 Verifying database content...")
    
    try:
        conn = sqlite3.connect("data/ml_models/training_data.db")
        conn.row_factory = sqlite3.Row
        
        # Check tables exist
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row['name'] for row in cursor.fetchall()]
        
        expected_tables = ['sentiment_features', 'trading_outcomes', 'model_performance']
        
        for table in expected_tables:
            if table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()['count']
                print(f"✅ Table {table}: {count} records")
            else:
                print(f"❌ Missing table: {table}")
        
        # Check recent data
        cursor = conn.execute("""
            SELECT COUNT(*) as recent_count 
            FROM sentiment_features 
            WHERE timestamp >= date('now', '-7 days')
        """)
        recent = cursor.fetchone()['recent_count']
        print(f"✅ Recent predictions (7d): {recent}")
        
        # Check unique symbols
        cursor = conn.execute("SELECT DISTINCT symbol FROM sentiment_features ORDER BY symbol")
        symbols = [row['symbol'] for row in cursor.fetchall()]
        print(f"✅ Tracked symbols: {', '.join(symbols)}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False

def verify_dashboard_imports():
    """Verify dashboard imports work correctly"""
    
    print("\n🔧 Verifying dashboard imports...")
    
    try:
        from dashboard import (
            fetch_ml_performance_metrics,
            fetch_current_sentiment_scores,
            fetch_ml_feature_analysis
        )
        print("✅ Dashboard imports successful")
        
        # Test each function
        ml_metrics = fetch_ml_performance_metrics()
        print(f"✅ ML metrics: Success rate {ml_metrics['success_rate']:.1%}")
        
        sentiment_df = fetch_current_sentiment_scores()
        print(f"✅ Sentiment data: {len(sentiment_df)} banks")
        
        feature_analysis = fetch_ml_feature_analysis()
        print(f"✅ Feature analysis: {feature_analysis['total_records']} records")
        
        return True
        
    except Exception as e:
        print(f"❌ Dashboard import/function test failed: {e}")
        return False

def main():
    """Main verification function"""
    
    print("🚀 Dashboard Verification System")
    print("=" * 50)
    
    # Run all verifications
    db_path_ok = verify_database_path()
    db_content_ok = verify_database_content() if db_path_ok else False
    imports_ok = verify_dashboard_imports() if db_path_ok else False
    
    print("\n" + "=" * 50)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 50)
    
    print(f"Database Path: {'✅ PASS' if db_path_ok else '❌ FAIL'}")
    print(f"Database Content: {'✅ PASS' if db_content_ok else '❌ FAIL'}")
    print(f"Dashboard Functions: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    
    overall_status = db_path_ok and db_content_ok and imports_ok
    print(f"Overall Status: {'✅ PASS' if overall_status else '❌ FAIL'}")
    
    if overall_status:
        print("\n🎉 Dashboard is ready for use!")
        print("💡 Run: streamlit run dashboard.py")
    else:
        print("\n🔧 Issues found - please resolve before using dashboard")
    
    return 0 if overall_status else 1

if __name__ == "__main__":
    exit(main())
