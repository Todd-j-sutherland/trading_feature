#!/usr/bin/env python3
"""
Test remote dashboard functionality
"""

import subprocess

def test_remote_dashboard():
    """Test that the dashboard starts without errors on remote"""
    
    print("🧪 Testing Remote Dashboard Functionality")
    print("=" * 50)
    
    cmd = [
        'ssh', 'root@170.64.199.151', 
        'cd /root/test && source dashboard_venv/bin/activate && python3 -c "from comprehensive_table_dashboard import TradingDataDashboard; d = TradingDataDashboard(\'/root/test\'); print(\'SUCCESS\')"'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0 and 'SUCCESS' in result.stdout:
        print("✅ REMOTE DASHBOARD TEST PASSED!")
        print(result.stdout)
        return True
    else:
        print("❌ REMOTE DASHBOARD TEST FAILED!")
        print("STDERR:", result.stderr)
        print("STDOUT:", result.stdout)
        return False

if __name__ == "__main__":
    success = test_remote_dashboard()
    if success:
        print("\n🚀 Ready to run dashboard on remote:")
        print("   ssh root@170.64.199.151")
        print("   cd /root/test")
        print("   source dashboard_venv/bin/activate")
        print("   streamlit run comprehensive_table_dashboard.py --server.port 8501")
    else:
        print("\n❌ Dashboard needs further fixes")
