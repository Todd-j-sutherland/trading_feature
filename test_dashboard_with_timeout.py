#!/usr/bin/env python3
"""
Dashboard Error Test with Timeout
Tests dashboard startup and runs for a short time to catch any runtime errors
"""

import subprocess
import time
import signal
import sys
from pathlib import Path

def test_dashboard_with_timeout():
    """Test dashboard startup with timeout to catch errors"""
    
    print("🔍 DASHBOARD ERROR TEST WITH TIMEOUT")
    print("=" * 50)
    
    try:
        # Test 1: Quick initialization test
        print("\n1️⃣ Testing dashboard initialization...")
        from comprehensive_table_dashboard import TradingDataDashboard
        
        root_dir = Path('.')
        dashboard = TradingDataDashboard(root_dir)
        print(f"✅ Dashboard initialized successfully")
        print(f"   Analysis results loaded: {'Yes' if dashboard.analysis_results else 'No'}")
        
        # Test 2: Test database connection
        print("\n2️⃣ Testing database operations...")
        if dashboard.main_db_path.exists():
            # Test a simple query
            df = dashboard.query_to_dataframe("SELECT COUNT(*) as count FROM sqlite_master WHERE type='table'")
            if not df.empty:
                table_count = df.iloc[0]['count']
                print(f"✅ Database queries working ({table_count} tables found)")
            else:
                print("⚠️ Database query returned empty result")
        else:
            print(f"⚠️ Database not found at {dashboard.main_db_path}")
        
        # Test 3: Start Streamlit dashboard with timeout
        print("\n3️⃣ Starting Streamlit dashboard with 10-second timeout...")
        print("   This will test for runtime errors during startup...")
        
        # Start the dashboard process
        process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", 
            "comprehensive_table_dashboard.py",
            "--server.headless", "true",
            "--server.port", "8502"  # Use different port to avoid conflicts
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait for 10 seconds or until process completes
        try:
            stdout, stderr = process.communicate(timeout=10)
            
            # If we get here, process completed (which is unexpected for streamlit)
            if process.returncode == 0:
                print("✅ Dashboard started and ran without errors")
            else:
                print(f"❌ Dashboard exited with error code: {process.returncode}")
                if stderr:
                    print(f"Error output: {stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            # This is expected - streamlit should keep running
            print("✅ Dashboard is running without immediate errors")
            
            # Terminate the process
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            
            # Check if there were any error messages in the brief run
            stdout, stderr = process.communicate()
            
            if stderr and "error" in stderr.lower():
                print(f"⚠️ Potential issues detected in stderr:")
                print(stderr)
                return False
            else:
                print("✅ No error messages detected during startup")
        
        print("\n✅ DASHBOARD ERROR TEST PASSED")
        print("🚀 Dashboard should be safe to run!")
        return True
        
    except ImportError as e:
        print(f"\n❌ IMPORT ERROR")
        print(f"Error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ DASHBOARD ERROR TEST FAILED")
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = test_dashboard_with_timeout()
    sys.exit(0 if success else 1)
