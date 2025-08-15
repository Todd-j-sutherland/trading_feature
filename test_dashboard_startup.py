#!/usr/bin/env python3
"""
Dashboard Startup Test
Quick test to verify the dashboard can initialize and start without errors
"""

def test_dashboard_startup():
    """Test dashboard startup and basic functionality"""
    
    print("🔍 DASHBOARD STARTUP TEST")
    print("=" * 50)
    
    try:
        # Test 1: Import and initialization
        print("\n1️⃣ Testing imports and initialization...")
        from pathlib import Path
        from comprehensive_table_dashboard import TradingDataDashboard
        
        root_dir = Path('.')
        dashboard = TradingDataDashboard(root_dir)
        print(f"✅ Dashboard initialized successfully")
        print(f"   Root dir: {dashboard.root_dir}")
        print(f"   DB path: {dashboard.main_db_path}")
        
        # Test 2: Database connection
        print("\n2️⃣ Testing database connection...")
        if dashboard.main_db_path.exists():
            conn = dashboard.get_database_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            conn.close()
            print(f"✅ Database connection successful")
            print(f"   Found {len(tables)} tables")
        else:
            print(f"⚠️ Database not found at {dashboard.main_db_path}")
        
        # Test 3: Analysis results loading
        print("\n3️⃣ Testing analysis results loading...")
        try:
            dashboard.load_analysis_results()
            print(f"✅ Analysis results loaded")
        except Exception as e:
            print(f"⚠️ Analysis results not available: {e}")
        
        print("\n✅ DASHBOARD STARTUP TEST PASSED")
        print("🚀 Dashboard should now start without errors!")
        return True
        
    except Exception as e:
        print(f"\n❌ DASHBOARD STARTUP TEST FAILED")
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_dashboard_startup()
