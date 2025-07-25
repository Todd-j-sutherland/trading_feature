#!/usr/bin/env python3
"""
Automated Reliable Data Collection Scheduler

This script should be run periodically to maintain reliable data quality
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

def run_data_collection_cycle():
    """Run a complete data collection and validation cycle"""
    
    print("🔄 AUTOMATED RELIABLE DATA COLLECTION CYCLE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    success = True
    
    try:
        # Step 1: Collect new reliable data
        print("1️⃣ Collecting new reliable sentiment data...")
        result = subprocess.run([sys.executable, "collect_reliable_data.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Data collection successful")
        else:
            print(f"❌ Data collection failed: {result.stderr}")
            success = False
        
        # Step 2: Validate data quality
        print("\n2️⃣ Validating data quality...")
        result = subprocess.run([sys.executable, "export_and_validate_metrics.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Data validation passed")
        else:
            print(f"❌ Data validation failed: {result.stderr}")
            success = False
        
        # Step 3: Verify dashboard functionality
        print("\n3️⃣ Verifying dashboard functionality...")
        result = subprocess.run([sys.executable, "verify_dashboard.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dashboard verification passed")
        else:
            print(f"❌ Dashboard verification failed: {result.stderr}")
            success = False
        
    except Exception as e:
        print(f"❌ Cycle failed with exception: {e}")
        success = False
    
    print(f"\n🎯 CYCLE COMPLETE")
    print("=" * 60)
    
    if success:
        print("✅ All systems operational - reliable data maintained")
        print("💡 Dashboard ready at: http://localhost:8501")
    else:
        print("❌ Issues detected - manual intervention may be required")
    
    return success

if __name__ == "__main__":
    success = run_data_collection_cycle()
    sys.exit(0 if success else 1)
