#!/usr/bin/env python3
"""
Simple Status Checker for Remote Trading System
"""

import sys
import os
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path

def check_environment():
    """Check virtual environment and packages"""
    print("🔍 ENVIRONMENT CHECK")
    print("=" * 40)
    
    # Check Python version
    print(f"🐍 Python Version: {sys.version.split()[0]}")
    
    # Check virtual environment
    venv_path = os.environ.get('VIRTUAL_ENV', 'Not activated')
    print(f"🌐 Virtual Environment: {venv_path}")
    
    # Test key packages
    packages = [
        'pandas', 'numpy', 'sklearn', 'transformers', 
        'yfinance', 'streamlit', 'fastapi'
    ]
    
    working_packages = 0
    for package in packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
            working_packages += 1
        except ImportError:
            print(f"  ❌ {package}")
    
    print(f"📊 Packages: {working_packages}/{len(packages)} working")
    return working_packages == len(packages)

def check_database():
    """Check database status"""
    print("\n🔍 DATABASE CHECK")
    print("=" * 40)
    
    db_path = "/root/trading_feature/data/trading_predictions.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📊 Tables found: {len(tables)}")
        
        for table in tables[:5]:  # Show first 5 tables
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  📋 {table}: {count} records")
        
        conn.close()
        print("✅ Database accessible")
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def check_system_health():
    """Check overall system health"""
    print("\n🔍 SYSTEM HEALTH CHECK")
    print("=" * 40)
    
    # Check disk space
    try:
        result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                fields = lines[1].split()
                if len(fields) >= 4:
                    print(f"💾 Disk Space: {fields[2]} used, {fields[3]} available")
        else:
            print("⚠️ Could not check disk space")
    except:
        print("⚠️ Could not check disk space")
    
    # Check memory
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if line.startswith('MemTotal:'):
                    total = line.split()[1]
                    print(f"💽 Memory Total: {int(total)//1024} MB")
                elif line.startswith('MemAvailable:'):
                    available = line.split()[1]
                    print(f"💽 Memory Available: {int(available)//1024} MB")
                    break
    except:
        print("⚠️ Could not check memory")
    
    # Check CPU load
    try:
        with open('/proc/loadavg', 'r') as f:
            load = f.read().split()[0]
            print(f"⚡ CPU Load: {load}")
    except:
        print("⚠️ Could not check CPU load")

def check_ml_models():
    """Check ML model availability"""
    print("\n🔍 ML MODELS CHECK")
    print("=" * 40)
    
    try:
        from transformers import pipeline
        
        # Test sentiment analysis model (lightweight)
        print("🧠 Testing sentiment analysis...")
        classifier = pipeline("sentiment-analysis", return_all_scores=True)
        result = classifier("The stock market is performing well today")
        print(f"  ✅ Sentiment model working: {result[0][0]['label']}")
        return True
        
    except Exception as e:
        print(f"❌ ML model test failed: {e}")
        return False

def main():
    """Main status check"""
    print("🎯 REMOTE TRADING SYSTEM STATUS CHECK")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    checks = {
        'Environment': check_environment(),
        'Database': check_database(),
        'ML Models': check_ml_models()
    }
    
    # System health (non-critical)
    check_system_health()
    
    # Summary
    print("\n📊 STATUS SUMMARY")
    print("=" * 30)
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check_name, status in checks.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {check_name}")
    
    print(f"\n🎯 Overall Status: {passed}/{total} checks passed")
    
    if passed == total:
        print("✅ Remote system is fully functional!")
        return True
    else:
        print("⚠️ Some issues detected - see details above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
