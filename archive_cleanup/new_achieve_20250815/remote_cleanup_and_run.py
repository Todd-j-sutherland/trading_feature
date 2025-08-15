#!/usr/bin/env python3
"""
Remote cleanup script to:
1. Remove test records with entry_price = 0
2. Run enhanced morning analyzer with real market data
3. Verify the results
"""

import subprocess
import sys
from datetime import datetime

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

def cleanup_test_records():
    """Remove test records with entry_price = 0 from remote database"""
    print("🧹 CLEANING UP TEST RECORDS")
    print("=" * 50)
    
    # First, show what will be deleted
    print("\n📋 Records to be deleted:")
    code, stdout, stderr = run_ssh_command(f"""
        cd {REMOTE_DIR} && 
        source {REMOTE_VENV}/bin/activate && 
        sqlite3 data/trading_predictions.db "SELECT symbol, predicted_action, action_confidence, prediction_timestamp FROM predictions WHERE entry_price = 0 ORDER BY prediction_timestamp DESC;"
    """)
    
    if code == 0:
        print(stdout)
        
        # Count records before deletion
        code2, stdout2, stderr2 = run_ssh_command(f"""
            cd {REMOTE_DIR} && 
            source {REMOTE_VENV}/bin/activate && 
            sqlite3 data/trading_predictions.db "SELECT COUNT(*) FROM predictions WHERE entry_price = 0;"
        """)
        
        if code2 == 0:
            test_count = stdout2.strip()
            print(f"\n🗑️  Will delete {test_count} test records with entry_price = 0")
            
            # Delete the test records
            print("\n🔥 Deleting test records...")
            code3, stdout3, stderr3 = run_ssh_command(f"""
                cd {REMOTE_DIR} && 
                source {REMOTE_VENV}/bin/activate && 
                sqlite3 data/trading_predictions.db "DELETE FROM predictions WHERE entry_price = 0;"
            """)
            
            if code3 == 0:
                print("✅ Test records deleted successfully")
                
                # Verify deletion
                code4, stdout4, stderr4 = run_ssh_command(f"""
                    cd {REMOTE_DIR} && 
                    source {REMOTE_VENV}/bin/activate && 
                    sqlite3 data/trading_predictions.db "SELECT COUNT(*) FROM predictions;"
                """)
                
                if code4 == 0:
                    remaining_count = stdout4.strip()
                    print(f"📊 Remaining predictions: {remaining_count}")
                    return True
            else:
                print(f"❌ Failed to delete test records: {stderr3}")
                return False
        else:
            print(f"❌ Failed to count test records: {stderr2}")
            return False
    else:
        print(f"❌ Failed to query test records: {stderr}")
        return False

def run_enhanced_morning_analyzer():
    """Run the enhanced morning analyzer with real market data"""
    print("\n🌅 RUNNING ENHANCED MORNING ANALYZER WITH REAL DATA")
    print("=" * 60)
    
    # Remove the SKIP_TRANSFORMERS environment variable to get real data
    print("🚀 Starting enhanced morning analyzer with real market data...")
    code, stdout, stderr = run_ssh_command(f"""
        cd {REMOTE_DIR} && 
        source {REMOTE_VENV}/bin/activate && 
        export PYTHONPATH={REMOTE_DIR} && 
        timeout 600 python enhanced_morning_analyzer_with_ml.py
    """)
    
    if code == 0:
        print("✅ Enhanced morning analyzer completed successfully!")
        
        # Show last few lines of output
        lines = stdout.strip().split('\n')
        print("\n📋 Last 15 lines of output:")
        for line in lines[-15:]:
            print(f"   {line}")
        
        return True
    else:
        print(f"❌ Enhanced morning analyzer failed: {stderr}")
        print(f"📋 Output: {stdout}")
        return False

def verify_real_data():
    """Verify that real market data was captured"""
    print("\n🔍 VERIFYING REAL MARKET DATA")
    print("=" * 50)
    
    # Check total predictions
    code, stdout, stderr = run_ssh_command(f"""
        cd {REMOTE_DIR} && 
        source {REMOTE_VENV}/bin/activate && 
        sqlite3 data/trading_predictions.db "SELECT COUNT(*) FROM predictions;"
    """)
    
    if code == 0:
        total_predictions = stdout.strip()
        print(f"📊 Total predictions: {total_predictions}")
    
    # Check valid predictions with entry prices > 0
    code2, stdout2, stderr2 = run_ssh_command(f"""
        cd {REMOTE_DIR} && 
        source {REMOTE_VENV}/bin/activate && 
        sqlite3 data/trading_predictions.db "SELECT COUNT(*) FROM predictions WHERE entry_price > 0;"
    """)
    
    if code2 == 0:
        valid_predictions = stdout2.strip()
        print(f"💰 Valid predictions (entry_price > 0): {valid_predictions}")
    
    # Show latest predictions with real prices
    print("\n📋 Latest predictions with real entry prices:")
    code3, stdout3, stderr3 = run_ssh_command(f"""
        cd {REMOTE_DIR} && 
        source {REMOTE_VENV}/bin/activate && 
        sqlite3 data/trading_predictions.db "SELECT symbol, predicted_action, ROUND(action_confidence, 3) as confidence, ROUND(entry_price, 2) as price, prediction_timestamp FROM predictions WHERE entry_price > 0 ORDER BY prediction_timestamp DESC LIMIT 8;"
    """)
    
    if code3 == 0:
        print(stdout3)
        
        # Check enhanced tables
        print("\n🧠 Enhanced ML data:")
        code4, stdout4, stderr4 = run_ssh_command(f"""
            cd {REMOTE_DIR} && 
            source {REMOTE_VENV}/bin/activate && 
            sqlite3 data/trading_predictions.db "SELECT COUNT(*) FROM enhanced_features;"
        """)
        
        code5, stdout5, stderr5 = run_ssh_command(f"""
            cd {REMOTE_DIR} && 
            source {REMOTE_VENV}/bin/activate && 
            sqlite3 data/trading_predictions.db "SELECT COUNT(*) FROM enhanced_outcomes;"
        """)
        
        if code4 == 0 and code5 == 0:
            enhanced_features = stdout4.strip()
            enhanced_outcomes = stdout5.strip()
            print(f"   Enhanced Features: {enhanced_features}")
            print(f"   Enhanced Outcomes: {enhanced_outcomes}")
            
            return True
    
    return False

def main():
    """Main cleanup and run function"""
    print("🚀 REMOTE CLEANUP AND REAL DATA RUN")
    print("=" * 60)
    print(f"📍 Remote Server: {REMOTE_HOST}")
    print(f"🕐 Start Time: {datetime.now()}")
    print()
    
    # Step 1: Cleanup test records
    if not cleanup_test_records():
        print("❌ Cleanup failed. Aborting.")
        return False
    
    # Step 2: Run enhanced morning analyzer with real data
    if not run_enhanced_morning_analyzer():
        print("❌ Enhanced morning analyzer failed. Continuing to verification...")
    
    # Step 3: Verify real data was captured
    verify_real_data()
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎯 CLEANUP AND REAL DATA RUN COMPLETE")
    print("=" * 60)
    print()
    print("🌐 Check Dashboard:")
    print(f"   Enhanced Dashboard: http://170.64.199.151:8501")
    print(f"   ML Dashboard: http://170.64.199.151:8502")
    print()
    print("📊 The dashboard should now show:")
    print("   - Real entry prices (not $0.00)")
    print("   - Accurate win rate calculations")
    print("   - Proper return calculations")
    print()
    
    return True

if __name__ == "__main__":
    main()
