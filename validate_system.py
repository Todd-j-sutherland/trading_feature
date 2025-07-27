#!/usr/bin/env python3
"""
Quick Data Validation Tool
Runs all available validation checks and provides a summary
"""

import os
import sys
import json
import glob
from datetime import datetime

def run_validation_summary():
    """Run a comprehensive validation summary"""
    print("🔍 ASX TRADING SYSTEM - DATA VALIDATION SUMMARY")
    print("=" * 60)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. Check latest validation files
    print("📁 VALIDATION FILES:")
    validation_files = glob.glob('metrics_exports/validation_*.txt')
    if validation_files:
        latest_file = max(validation_files)
        print(f"   ✅ Latest: {latest_file}")
        with open(latest_file, 'r') as f:
            content = f.read()
            if "PASS" in content:
                print("   ✅ Status: PASSING")
            else:
                print("   ❌ Status: ISSUES FOUND")
    else:
        print("   ❌ No validation files found")
    print()

    # 2. Check database files
    print("🗄️  DATABASE STATUS:")
    db_files = [
        'data/ml_models/training_data.db',
        'data/trading_data.db', 
        'morning_analysis.db'
    ]
    
    for db_file in db_files:
        if os.path.exists(db_file):
            size = os.path.getsize(db_file) / 1024 / 1024  # MB
            print(f"   ✅ {db_file}: {size:.1f} MB")
        else:
            print(f"   ❌ {db_file}: Missing")
    print()

    # 3. Check ML models
    print("🤖 ML MODELS:")
    model_files = glob.glob('data/ml_models/**/*.pkl', recursive=True)
    if model_files:
        print(f"   ✅ Found {len(model_files)} model files")
        for model in model_files[:5]:  # Show first 5
            print(f"      • {model}")
        if len(model_files) > 5:
            print(f"      ... and {len(model_files) - 5} more")
    else:
        print("   ❌ No ML model files found")
    print()

    # 4. Recent logs
    print("📝 RECENT ACTIVITY:")
    log_files = glob.glob('logs/*.log')
    if log_files:
        latest_log = max(log_files, key=os.path.getmtime)
        mod_time = datetime.fromtimestamp(os.path.getmtime(latest_log))
        print(f"   ✅ Latest log: {latest_log}")
        print(f"   📅 Last updated: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("   ❌ No log files found")
    print()

    # 5. System health
    print("🏥 SYSTEM HEALTH:")
    
    # Check if dashboard_env exists
    if os.path.exists('dashboard_env'):
        print("   ✅ Python environment: dashboard_env")
    else:
        print("   ❌ Python environment: Missing")
    
    # Check if frontend exists
    if os.path.exists('frontend'):
        print("   ✅ Frontend: Available")
    else:
        print("   ❌ Frontend: Missing")
    
    # Check main files
    main_files = ['api_server.py', 'dashboard.py', 'app/main.py']
    for file in main_files:
        if os.path.exists(file):
            print(f"   ✅ {file}: Available")
        else:
            print(f"   ❌ {file}: Missing")
    print()

    print("💡 NEXT STEPS:")
    print("   • Run 'python ml_data_validator.py' for detailed ML validation")
    print("   • Run 'python test_validation_framework.py' for comprehensive testing")
    print("   • Run 'python -m app.main evening' to generate new validation data")
    print("   • Check 'metrics_exports/' folder for detailed validation reports")

if __name__ == "__main__":
    run_validation_summary()
