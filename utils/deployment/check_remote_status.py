#!/usr/bin/env python3
"""
Remote Database Status Checker

Quick script to check if your remote database needs timestamp fixes.
Run this to verify the status before and after applying fixes.
"""

import subprocess
import json
from datetime import datetime

def check_remote_database_status():
    """Check if remote database has timestamp issues"""
    
    print("🔍 CHECKING REMOTE DATABASE STATUS")
    print("=" * 45)
    
    remote_host = "147.185.221.19"
    remote_user = "root"
    remote_db = "/root/test/data/trading_predictions.db"
    
    # Create a simple check script
    check_script = f'''
import sqlite3
from datetime import datetime

try:
    with sqlite3.connect("{remote_db}") as conn:
        cursor = conn.cursor()
        
        # Check total records
        cursor.execute("SELECT COUNT(*) FROM predictions")
        total_predictions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM enhanced_features") 
        total_features = cursor.fetchone()[0]
        
        # Check for data leakage
        cursor.execute("""
            SELECT COUNT(*) FROM predictions p
            JOIN enhanced_features ef ON p.symbol = ef.symbol
            WHERE datetime(ef.timestamp) > datetime(p.prediction_timestamp, '+1 hour')
        """)
        leakage_count = cursor.fetchone()[0]
        
        # Check for future predictions
        cursor.execute("""
            SELECT COUNT(*) FROM predictions
            WHERE prediction_timestamp > datetime('now')
        """)
        future_predictions = cursor.fetchone()[0]
        
        print(f"REMOTE_DB_STATUS:")
        print(f"Total predictions: {{total_predictions}}")
        print(f"Total features: {{total_features}}")
        print(f"Data leakage instances: {{leakage_count}}")
        print(f"Future predictions: {{future_predictions}}")
        
        if leakage_count == 0 and future_predictions == 0:
            print("STATUS: CLEAN")
        else:
            print("STATUS: NEEDS_FIXING")
            
except Exception as e:
    print(f"ERROR: {{e}}")
'''
    
    try:
        print(f"🌐 Connecting to {remote_host}...")
        
        # Try to run the check
        ssh_command = [
            "ssh", "-o", "ConnectTimeout=10", "-o", "StrictHostKeyChecking=no",
            f"{remote_user}@{remote_host}",
            f"cd /root/test && python3 -c '{check_script}'"
        ]
        
        result = subprocess.run(ssh_command, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Successfully connected to remote server")
            print("\n📊 Remote Database Status:")
            print(result.stdout)
            
            if "STATUS: CLEAN" in result.stdout:
                print("\n🏆 Remote database is already synchronized!")
                return True
            elif "STATUS: NEEDS_FIXING" in result.stdout:
                print("\n⚠️  Remote database needs timestamp fixes")
                print("💡 Run the remote_database_fixer.py on your server")
                return False
        else:
            print(f"❌ Connection failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("❌ Connection timed out")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n💡 Manual Check Instructions:")
    print("1. SSH to your remote server: ssh root@147.185.221.19")
    print("2. Navigate to: cd /root/test")
    print("3. Run the remote_database_fixer.py script")
    
    return None

def main():
    """Main function"""
    check_remote_database_status()

if __name__ == "__main__":
    main()
