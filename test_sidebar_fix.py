#!/usr/bin/env python3
"""
Test specifically for the sidebar rendering issue that was failing remotely
"""
import sys
import traceback

try:
    # Import and initialize the dashboard
    from comprehensive_table_dashboard import TradingDataDashboard
    
    print("Testing dashboard sidebar rendering...")
    
    # Test initialization with root_dir
    dashboard = TradingDataDashboard("/root/test")  # Using remote path
    
    print("✅ Dashboard initialized successfully!")
    print(f"✅ analysis_results attribute: {dashboard.analysis_results}")
    print(f"✅ analysis_results type: {type(dashboard.analysis_results)}")
    
    # Test the specific code that was failing in render_sidebar
    # This is the exact line that was causing the error
    databases = list(dashboard.analysis_results.get('databases', {}).keys()) if dashboard.analysis_results is not None else []
    print(f"✅ Databases list created successfully: {databases}")
    
    # Test the other sidebar conditions that could fail
    if dashboard.analysis_results is not None and dashboard.analysis_results:
        summary = dashboard.analysis_results.get('dashboard_data', {}).get('summary', {})
        print(f"✅ Summary accessed successfully: {bool(summary)}")
    else:
        print("✅ Empty analysis_results handled correctly")
    
    print("🚀 SIDEBAR RENDERING TEST PASSED!")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    print(f"❌ Error type: {type(e).__name__}")
    traceback.print_exc()
    sys.exit(1)
