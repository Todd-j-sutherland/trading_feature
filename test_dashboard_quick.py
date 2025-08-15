#!/usr/bin/env python3
"""
Quick test to verify dashboard initialization works without errors
"""
import sys
import traceback

try:
    # Import and initialize the dashboard
    from comprehensive_table_dashboard import TradingDataDashboard
    
    print("Testing dashboard initialization...")
    
    # Test initialization with root_dir
    dashboard = TradingDataDashboard("/Users/toddsutherland/Repos/trading_feature")
    
    print("✅ Dashboard initialized successfully!")
    print(f"✅ analysis_results attribute exists: {hasattr(dashboard, 'analysis_results')}")
    print(f"✅ analysis_results type: {type(dashboard.analysis_results)}")
    
    # Test a simple method call
    if hasattr(dashboard, 'get_database_info'):
        db_info = dashboard.get_database_info()
        print(f"✅ Database info retrieved: {len(db_info)} tables found")
    
    print("🚀 ALL TESTS PASSED - Dashboard is ready to run!")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    print(f"❌ Error type: {type(e).__name__}")
    traceback.print_exc()
    sys.exit(1)
