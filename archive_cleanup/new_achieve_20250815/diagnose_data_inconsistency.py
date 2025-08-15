#!/usr/bin/env python3
"""
Remote Data Inconsistency Diagnostic
Investigate why morning routine shows different data than database query
"""

import sqlite3
import os
from datetime import datetime

def diagnose_remote_inconsistency():
    """
    Diagnose the inconsistency between morning routine output and database reality
    """
    print("🔍 REMOTE DATA INCONSISTENCY DIAGNOSTIC")
    print("=" * 60)
    
    db_path = "data/ml_models/enhanced_training_data.db"
    
    print("📊 ISSUE ANALYSIS:")
    print("   Morning Routine Shows: Banks Analyzed: 7, Feature Pipeline: 371 features")
    print("   Database Query Shows:  Features: 187, Outcomes: 10")
    print("   Problem: Data inconsistency between runtime and storage\n")
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 DETAILED DATABASE ANALYSIS:")
        print("-" * 40)
        
        # 1. Check actual table contents
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📋 Tables in database: {[table[0] for table in tables]}")
        
        # 2. Enhanced features analysis
        cursor.execute("SELECT COUNT(*) FROM enhanced_features")
        total_features = cursor.fetchone()[0]
        print(f"\n📈 Enhanced Features Table:")
        print(f"   Total records: {total_features}")
        
        if total_features > 0:
            # Check feature distribution by symbol
            cursor.execute("""
                SELECT symbol, COUNT(*) as count, MIN(timestamp) as first, MAX(timestamp) as last
                FROM enhanced_features 
                GROUP BY symbol 
                ORDER BY count DESC
            """)
            symbol_stats = cursor.fetchall()
            
            print(f"   Symbol distribution:")
            for symbol, count, first_time, last_time in symbol_stats:
                print(f"     {symbol}: {count} records ({first_time} to {last_time})")
            
            # Check recent vs total features
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN timestamp >= datetime('now', '-1 day') THEN 1 END) as last_24h,
                    COUNT(CASE WHEN timestamp >= datetime('now', '-7 days') THEN 1 END) as last_7d
                FROM enhanced_features
            """)
            time_stats = cursor.fetchone()
            print(f"   Time distribution:")
            print(f"     Total: {time_stats[0]}")
            print(f"     Last 24h: {time_stats[1]}")
            print(f"     Last 7 days: {time_stats[2]}")
        
        # 3. Enhanced outcomes analysis
        cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes")
        total_outcomes = cursor.fetchone()[0]
        print(f"\n📉 Enhanced Outcomes Table:")
        print(f"   Total records: {total_outcomes}")
        
        cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes WHERE price_direction_1h IS NOT NULL")
        outcomes_with_data = cursor.fetchone()[0]
        print(f"   With price data: {outcomes_with_data}")
        
        # 4. Check for data source confusion
        print(f"\n🔍 POTENTIAL CAUSES:")
        
        # Check if morning routine is writing to a different location
        possible_paths = [
            "data/ml_models/enhanced_training_data.db",
            "./enhanced_training_data.db",
            "enhanced_training_data.db",
            "data/enhanced_training_data.db",
            "morning_analysis.db"
        ]
        
        print(f"   📁 Checking for multiple database files:")
        for path in possible_paths:
            if os.path.exists(path):
                stat = os.stat(path)
                print(f"     ✅ {path} (size: {stat.st_size:,} bytes, modified: {datetime.fromtimestamp(stat.st_mtime)})")
            else:
                print(f"     ❌ {path} (not found)")
        
        # Check for in-memory data vs persistent data
        print(f"\n   🧠 POSSIBLE EXPLANATIONS:")
        print("   1. Morning routine using in-memory data that's not persisted")
        print("   2. Multiple database files with different data")
        print("   3. Caching layer showing stale data")
        print("   4. Feature calculation vs database storage mismatch")
        print("   5. Working directory differences between morning routine and query")
        
        # 5. Check working directory and path issues
        print(f"\n📂 ENVIRONMENT CHECK:")
        print(f"   Current working directory: {os.getcwd()}")
        print(f"   Database path resolved to: {os.path.abspath(db_path)}")
        print(f"   Database exists: {os.path.exists(db_path)}")
        
        if os.path.exists(db_path):
            stat = os.stat(db_path)
            print(f"   Database size: {stat.st_size:,} bytes")
            print(f"   Last modified: {datetime.fromtimestamp(stat.st_mtime)}")
        
        # 6. Memory vs storage analysis
        print(f"\n💭 MEMORY VS STORAGE ANALYSIS:")
        print("   If morning routine shows 371 features but database has 187:")
        print("   → Features are calculated in-memory but not all are saved")
        print("   → Morning analyzer might be using cached/temporary data")
        print("   → Database write operation might be incomplete")
        
        conn.close()
        
        # 7. Recommendations
        print(f"\n💡 DIAGNOSTIC RECOMMENDATIONS:")
        print("   1. Check if morning routine is writing to correct database path")
        print("   2. Verify working directory when running morning analysis")
        print("   3. Look for database transaction commit issues")
        print("   4. Check if features are calculated but not persisted")
        print("   5. Examine morning analyzer code for data storage logic")
        
        return True
        
    except Exception as e:
        print(f"❌ Diagnostic error: {e}")
        return False

def create_path_verification_script():
    """
    Create script to verify database paths and data consistency
    """
    print(f"\n🔧 Creating path verification script...")
    
    script_content = '''#!/usr/bin/env python3
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
    
    print(f"\\n📁 Database file search:")
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
        print(f"\\n📊 Analyzing: {db_path}")
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
'''
    
    with open("verify_remote_paths.py", "w") as f:
        f.write(script_content)
    
    print("   ✅ Created: verify_remote_paths.py")
    print("   📤 Upload this to remote server and run:")
    print("   ssh root@170.64.199.151")
    print("   cd /root/test && python3 verify_remote_paths.py")

if __name__ == "__main__":
    diagnose_remote_inconsistency()
    create_path_verification_script()
    
    print(f"\n" + "=" * 60)
    print("🎯 SUMMARY:")
    print("📊 Morning routine shows 371 features, database query shows 187")
    print("🔍 This suggests data inconsistency between calculation and storage")
    print("💡 Run verify_remote_paths.py on remote server to diagnose")
    print("=" * 60)
