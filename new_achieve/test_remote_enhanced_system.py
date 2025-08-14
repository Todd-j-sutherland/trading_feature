#!/usr/bin/env python3
"""
Remote Testing Script for Enhanced Database Architecture
Tests the enhanced ML system on the remote server
"""

import subprocess
import sys
import json
import os
from datetime import datetime
from pathlib import Path

# Remote server configuration
REMOTE_HOST = "root@170.64.199.151"
REMOTE_DIR = "/root/test"
REMOTE_VENV = "/root/trading_venv"
SSH_KEY = "~/.ssh/id_rsa"

def run_ssh_command(command, capture_output=True):
    """Execute SSH command on remote server"""
    ssh_cmd = f'ssh -i {SSH_KEY} {REMOTE_HOST} "{command}"'
    print(f"🔧 Executing: {command}")
    
    try:
        result = subprocess.run(ssh_cmd, shell=True, capture_output=capture_output, text=True)
        if capture_output:
            return result.returncode, result.stdout, result.stderr
        else:
            return result.returncode, "", ""
    except Exception as e:
        print(f"❌ SSH command failed: {e}")
        return 1, "", str(e)

def check_remote_environment():
    """Check remote server environment and resources"""
    print("🔍 CHECKING REMOTE ENVIRONMENT")
    print("=" * 50)
    
    # Check server resources
    print("\n📊 Server Resources:")
    code, stdout, stderr = run_ssh_command("free -h && echo '---' && df -h /")
    if code == 0:
        print(stdout)
    else:
        print(f"❌ Resource check failed: {stderr}")
        return False
    
    # Check Python environment
    print("\n🐍 Python Environment:")
    code, stdout, stderr = run_ssh_command(f"cd {REMOTE_DIR} && source {REMOTE_VENV}/bin/activate && python --version && pip list | grep -E 'streamlit|pandas|sqlite|plotly'")
    if code == 0:
        print(stdout)
    else:
        print(f"❌ Python environment check failed: {stderr}")
        return False
    
    return True

def upload_enhanced_files():
    """Upload the enhanced database architecture files to remote"""
    print("\n📤 UPLOADING ENHANCED FILES")
    print("=" * 50)
    
    files_to_upload = [
        "enhanced_ml_dashboard.py",
        "ml_dashboard.py", 
        "enhanced_morning_analyzer_with_ml.py",
        "enhanced_evening_analyzer_with_ml.py",
        "technical_analysis_engine.py"
    ]
    
    for file in files_to_upload:
        if Path(file).exists():
            print(f"📤 Uploading {file}...")
            cmd = f"scp -i {SSH_KEY} {file} {REMOTE_HOST}:{REMOTE_DIR}/"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {file} uploaded successfully")
            else:
                print(f"❌ Failed to upload {file}: {result.stderr}")
                return False
        else:
            print(f"⚠️ {file} not found locally")
    
    # Upload database if it exists locally
    if Path("data/trading_predictions.db").exists():
        print("📤 Uploading enhanced database...")
        cmd = f"scp -i {SSH_KEY} data/trading_predictions.db {REMOTE_HOST}:{REMOTE_DIR}/data/"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Enhanced database uploaded successfully")
        else:
            print(f"⚠️ Database upload failed: {result.stderr}")
    
    return True

def test_remote_enhanced_system():
    """Test the enhanced ML system on remote server"""
    print("\n🧪 TESTING ENHANCED SYSTEM REMOTELY")
    print("=" * 50)
    
    # Test enhanced morning analyzer
    print("\n🌅 Testing Enhanced Morning Analyzer:")
    code, stdout, stderr = run_ssh_command(f"""
        cd {REMOTE_DIR} && 
        source {REMOTE_VENV}/bin/activate && 
        export PYTHONPATH={REMOTE_DIR} && 
        export SKIP_TRANSFORMERS=1 && 
        timeout 300 python enhanced_morning_analyzer_with_ml.py
    """)
    
    if code == 0:
        print("✅ Enhanced morning analyzer completed successfully")
        # Show last few lines of output
        lines = stdout.strip().split('\n')
        print("📋 Last few lines of output:")
        for line in lines[-10:]:
            print(f"   {line}")
    else:
        print(f"❌ Enhanced morning analyzer failed: {stderr}")
        print(f"📋 Output: {stdout}")
    
    # Check database state
    print("\n🗄️ Checking Enhanced Database:")
    code, stdout, stderr = run_ssh_command(f"cd {REMOTE_DIR} && source {REMOTE_VENV}/bin/activate && sqlite3 data/trading_predictions.db '.tables'")
    
    if code == 0:
        print("✅ Database tables found:")
        print(stdout)
        
        # Now check record counts with separate commands
        print("\n📊 Database Record Counts:")
        tables_to_check = [
            ("enhanced_features", "Enhanced Features"),
            ("enhanced_outcomes", "Enhanced Outcomes"), 
            ("predictions", "All Predictions")
        ]
        
        for table, label in tables_to_check:
            code2, stdout2, stderr2 = run_ssh_command(f"cd {REMOTE_DIR} && source {REMOTE_VENV}/bin/activate && sqlite3 data/trading_predictions.db 'SELECT COUNT(*) FROM {table};'")
            if code2 == 0:
                count = stdout2.strip()
                print(f"   {label}: {count}")
            else:
                print(f"   {label}: Error - {stderr2}")
                
        # Check for valid predictions with entry prices
        print("\n💰 Entry Price Validation:")
        code3, stdout3, stderr3 = run_ssh_command(f"cd {REMOTE_DIR} && source {REMOTE_VENV}/bin/activate && sqlite3 data/trading_predictions.db 'SELECT COUNT(*) FROM predictions WHERE entry_price > 0;'")
        if code3 == 0:
            valid_count = stdout3.strip()
            print(f"   Valid Predictions (entry_price > 0): {valid_count}")
        
    else:
        print(f"❌ Database query failed: {stderr}")
    
    return code == 0

def start_remote_dashboards():
    """Start both dashboards on remote server"""
    print("\n🎯 STARTING REMOTE DASHBOARDS")
    print("=" * 50)
    
    # Kill any existing streamlit processes
    print("🛑 Stopping existing dashboards...")
    run_ssh_command("pkill -f streamlit", capture_output=False)
    
    # Start enhanced dashboard on port 8501
    print("🚀 Starting Enhanced Dashboard on port 8501...")
    code, stdout, stderr = run_ssh_command(f"""
        cd {REMOTE_DIR} && 
        source {REMOTE_VENV}/bin/activate && 
        export PYTHONPATH={REMOTE_DIR} && 
        nohup streamlit run enhanced_ml_dashboard.py --server.port 8501 --server.address 0.0.0.0 > dashboard_enhanced.log 2>&1 &
    """, capture_output=False)
    
    # Start ML dashboard on port 8502  
    print("🚀 Starting ML Dashboard on port 8502...")
    code, stdout, stderr = run_ssh_command(f"""
        cd {REMOTE_DIR} && 
        source {REMOTE_VENV}/bin/activate && 
        export PYTHONPATH={REMOTE_DIR} && 
        nohup streamlit run ml_dashboard.py --server.port 8502 --server.address 0.0.0.0 > dashboard_ml.log 2>&1 &
    """, capture_output=False)
    
    # Wait and check if dashboards started
    print("⏳ Waiting for dashboards to start...")
    import time
    time.sleep(10)
    
    code, stdout, stderr = run_ssh_command("ps aux | grep streamlit | grep -v grep")
    if code == 0 and "streamlit" in stdout:
        print("✅ Dashboards started successfully:")
        print(stdout)
        return True
    else:
        print("❌ Dashboards failed to start")
        return False

def check_remote_dashboard_access():
    """Check if dashboards are accessible"""
    print("\n🌐 CHECKING DASHBOARD ACCESS")
    print("=" * 50)
    
    # Check dashboard processes
    code, stdout, stderr = run_ssh_command("netstat -tlnp | grep :850")
    if code == 0:
        print("✅ Dashboard ports are listening:")
        print(stdout)
    else:
        print("❌ Dashboard ports not accessible")
    
    # Check dashboard logs
    print("\n📋 Enhanced Dashboard Log (last 10 lines):")
    code, stdout, stderr = run_ssh_command(f"cd {REMOTE_DIR} && tail -10 dashboard_enhanced.log")
    if code == 0:
        print(stdout)
    
    print("\n📋 ML Dashboard Log (last 10 lines):")
    code, stdout, stderr = run_ssh_command(f"cd {REMOTE_DIR} && tail -10 dashboard_ml.log")
    if code == 0:
        print(stdout)
    
    return True

def run_remote_data_verification():
    """Run data verification on remote server"""
    print("\n🔍 REMOTE DATA VERIFICATION")
    print("=" * 50)
    
    # Upload our verification script
    if Path("final_success_verification.py").exists():
        print("📤 Uploading verification script...")
        cmd = f"scp -i {SSH_KEY} final_success_verification.py {REMOTE_HOST}:{REMOTE_DIR}/"
        subprocess.run(cmd, shell=True)
        
        # Run verification
        print("🧪 Running remote verification...")
        code, stdout, stderr = run_ssh_command(f"""
            cd {REMOTE_DIR} && 
            source {REMOTE_VENV}/bin/activate && 
            python final_success_verification.py
        """)
        
        if code == 0:
            print("✅ Remote verification successful:")
            print(stdout)
        else:
            print(f"❌ Remote verification failed: {stderr}")
        
        return code == 0
    else:
        print("⚠️ Verification script not found locally")
        return False

def main():
    """Main remote testing function"""
    print("🚀 REMOTE TESTING - ENHANCED ML SYSTEM")
    print("=" * 60)
    print(f"📍 Remote Server: {REMOTE_HOST}")
    print(f"📁 Remote Directory: {REMOTE_DIR}")
    print(f"🕐 Test Time: {datetime.now()}")
    print()
    
    # Step 1: Check remote environment
    if not check_remote_environment():
        print("❌ Remote environment check failed. Aborting.")
        return False
    
    # Step 2: Upload enhanced files
    if not upload_enhanced_files():
        print("❌ File upload failed. Aborting.")
        return False
    
    # Step 3: Test enhanced system
    if not test_remote_enhanced_system():
        print("⚠️ Enhanced system test had issues, but continuing...")
    
    # Step 4: Start dashboards
    if not start_remote_dashboards():
        print("⚠️ Dashboard startup had issues, but continuing...")
    
    # Step 5: Check dashboard access
    check_remote_dashboard_access()
    
    # Step 6: Run data verification
    run_remote_data_verification()
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎯 REMOTE TESTING COMPLETE")
    print("=" * 60)
    print()
    print("🌐 Dashboard URLs:")
    print(f"   Enhanced Dashboard: http://{REMOTE_HOST.split('@')[1]}:8501")
    print(f"   ML Dashboard: http://{REMOTE_HOST.split('@')[1]}:8502")
    print()
    print("🔧 Remote Commands:")
    print(f"   SSH Access: ssh -i {SSH_KEY} {REMOTE_HOST}")
    print(f"   Check Logs: ssh -i {SSH_KEY} {REMOTE_HOST} 'cd {REMOTE_DIR} && tail -f dashboard_*.log'")
    print(f"   Check DB: ssh -i {SSH_KEY} {REMOTE_HOST} 'cd {REMOTE_DIR} && sqlite3 data/trading_predictions.db .tables'")
    print()
    
    return True

if __name__ == "__main__":
    main()
