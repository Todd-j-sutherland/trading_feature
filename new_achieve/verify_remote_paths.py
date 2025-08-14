#!/usr/bin/env python3
"""
Remote Path and Data Verification Script
Run this on remote server to verify database paths and data consistency
"""

import os
import sqlite3
from datetime import datetime

def verify_remote_paths():
    """Verify database paths and data on remote server"""
    print("🔍 REMOTE PATH VERIFICATION")
    print("=" * 40)
    
    # Check current environment
    print(f"📂 Environment:")
    print(f"   Working directory: {os.getcwd()}")
    print(f"   Home directory: {os.path.expanduser('~')}")
    
    # Check for database files
    search_paths = [
        "data/ml_models/enhanced_training_data.db",
        "./data/ml_models/enhanced_training_data.db", 
        "/root/test/data/ml_models/enhanced_training_data.db",
        "enhanced_training_data.db",
        "morning_analysis.db"
    ]
    
    print(f"\n📁 Database file search:")
    found_dbs = []
    
    for path in search_paths:
        abs_path = os.path.abspath(path)
        if os.path.exists(path):
            stat = os.stat(path)
            print(f"   ✅ {path}")
            print(f"      → {abs_path}")
            print(f"      → Size: {stat.st_size:,} bytes")
            print(f"      → Modified: {datetime.fromtimestamp(stat.st_mtime)}")
            found_dbs.append(path)
        else:
            print(f"   ❌ {path} (not found)")
    
    # Analyze each found database
    for db_path in found_dbs:
        print(f"\n📊 Analyzing: {db_path}")
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM enhanced_features")
            features = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes WHERE price_direction_1h IS NOT NULL")
            outcomes = cursor.fetchone()[0]
            
            print(f"   Features: {features}")
            print(f"   Outcomes: {outcomes}")
            print(f"   Training ready: {'✅ YES' if features >= 50 and outcomes >= 50 else '❌ NO'}")
            
            conn.close()
            
        except Exception as e:
            print(f"   ❌ Error reading database: {e}")

if __name__ == "__main__":
    verify_remote_paths()
