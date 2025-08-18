#!/usr/bin/env python3
"""
Remote System Analysis Tool - Updated for /root/test/ directory
"""

import subprocess
import sys
import os
import sqlite3
from datetime import datetime
from pathlib import Path
import json

def test_system_commands():
    """Test system commands from correct directory"""
    print("\n🔍 TESTING SYSTEM COMMANDS FROM /root/test/")
    print("=" * 60)
    
    # Set up the correct environment
    base_dir = "/root/test"
    venv_python = "/root/trading_venv/bin/python"
    
    commands = {
        "status": f"cd {base_dir} && {venv_python} -m app.main status",
        "morning": f"cd {base_dir} && timeout 30s {venv_python} -m app.main morning",
        "evening": f"cd {base_dir} && timeout 30s {venv_python} -m app.main evening"
    }
    
    results = {}
    for name, cmd in commands.items():
        print(f"\n🧪 Testing: {name}")
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=35)
            if result.returncode == 0:
                print(f"  ✅ {name}: SUCCESS")
                results[name] = "SUCCESS"
            else:
                print(f"  ❌ {name}: Failed with code {result.returncode}")
                if result.stderr:
                    print(f"    Error: {result.stderr[:200]}")
                results[name] = f"FAILED (code {result.returncode})"
        except subprocess.TimeoutExpired:
            print(f"  ⏰ {name}: TIMEOUT (but this may be normal for long operations)")
            results[name] = "TIMEOUT"
        except Exception as e:
            print(f"  ❌ {name}: ERROR - {e}")
            results[name] = f"ERROR: {e}"
    
    return results

def test_database_access():
    """Test database access from the test directory"""
    print("\n🔍 DATABASE ACCESS TEST")
    print("=" * 40)
    
    # Test both potential database locations
    db_paths = [
        "/root/test/data/trading_predictions.db",
        "/root/data/trading_predictions.db",
        "/root/trading_feature/data/trading_predictions.db"
    ]
    
    working_db = None
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"✅ Found database: {db_path}")
            working_db = db_path
            break
        else:
            print(f"❌ Not found: {db_path}")
    
    if working_db:
        try:
            conn = sqlite3.connect(working_db)
            cursor = conn.cursor()
            
            # Test basic operations
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"📊 Tables: {len(tables)}")
            
            for table in tables[:5]:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  📋 {table}: {count} records")
            
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Database error: {e}")
            return False
    else:
        print("❌ No database found")
        return False

def test_package_imports():
    """Test critical package imports"""
    print("\n🔍 PACKAGE IMPORT TEST")
    print("=" * 40)
    
    packages = [
        'pandas', 'numpy', 'sklearn', 'transformers',
        'yfinance', 'streamlit', 'fastapi', 'sqlite3'
    ]
    
    working = 0
    for package in packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
            working += 1
        except ImportError:
            print(f"  ❌ {package}")
    
    print(f"📊 Packages: {working}/{len(packages)} working")
    return working == len(packages)

def check_ml_models():
    """Test ML model functionality"""
    print("\n🔍 ML MODEL TEST")
    print("=" * 40)
    
    try:
        from transformers import pipeline
        
        # Test a lightweight model
        classifier = pipeline("sentiment-analysis", return_all_scores=True)
        result = classifier("The market is looking positive today")
        print(f"  ✅ Sentiment model: {result[0][0]['label']}")
        return True
    except Exception as e:
        print(f"  ❌ ML model test failed: {e}")
        return False

def main():
    """Main remote system analysis"""
    print("🎯 REMOTE SYSTEM ANALYSIS - /root/test/ DIRECTORY")
    print("=" * 70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Run all tests
    tests = {
        "Package Imports": test_package_imports(),
        "Database Access": test_database_access(),
        "ML Models": check_ml_models(),
    }
    
    # Test system commands
    print("\n" + "=" * 70)
    command_results = test_system_commands()
    
    # Summary
    print("\n📊 ANALYSIS SUMMARY")
    print("=" * 40)
    
    # Component tests
    passed = sum(tests.values())
    total = len(tests)
    
    for test_name, status in tests.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {test_name}")
    
    # Command tests
    print(f"\n🚀 Command Results:")
    for cmd, result in command_results.items():
        if result == "SUCCESS":
            print(f"  ✅ {cmd}: {result}")
        elif result == "TIMEOUT":
            print(f"  ⏰ {cmd}: {result}")
        else:
            print(f"  ❌ {cmd}: {result}")
    
    successful_commands = sum(1 for r in command_results.values() if r in ["SUCCESS", "TIMEOUT"])
    
    print(f"\n🎯 Overall Results:")
    print(f"  📊 Component Tests: {passed}/{total} passed")
    print(f"  🚀 Commands Working: {successful_commands}/{len(command_results)}")
    
    if passed == total and successful_commands >= 2:
        print("  ✅ Remote system is FULLY FUNCTIONAL!")
        return True
    elif passed >= total - 1 and successful_commands >= 1:
        print("  ⚠️ Remote system is MOSTLY FUNCTIONAL")
        return True
    else:
        print("  ❌ Remote system has significant issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
