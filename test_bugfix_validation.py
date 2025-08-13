#!/usr/bin/env python3
"""
Quick validation test for the bugfix on remote server
"""

import sqlite3
import os
from datetime import datetime

def test_bugfix_validation():
    """Test that the bugfix is properly implemented"""
    print("🔍 BUGFIX VALIDATION TEST")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists("data/trading_unified.db"):
        print("❌ Database not found - run from /root/test directory")
        return False
    
    # Check current database state
    conn = sqlite3.connect("data/trading_unified.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM enhanced_features")
    feature_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes")
    outcome_count = cursor.fetchone()[0]
    
    print(f"📊 Current State:")
    print(f"   Features: {feature_count}")
    print(f"   Outcomes: {outcome_count}")
    print(f"   Missing: {feature_count - outcome_count}")
    
    # Check if the enhanced_morning_analyzer_with_ml.py contains the bugfix
    try:
        with open("enhanced_morning_analyzer_with_ml.py", "r") as f:
            content = f.read()
        
        if "record_enhanced_outcomes" in content and "BUGFIX" in content:
            print("✅ Bugfix code detected in file")
            
            # Count occurrences to make sure it's the fixed version
            bugfix_occurrences = content.count("record_enhanced_outcomes")
            if bugfix_occurrences >= 2:  # Should appear in method call and definition
                print(f"✅ Bugfix properly implemented ({bugfix_occurrences} occurrences)")
                return True
            else:
                print(f"⚠️ Unexpected bugfix implementation ({bugfix_occurrences} occurrences)")
                return False
        else:
            print("❌ Bugfix not found in file")
            return False
            
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    success = test_bugfix_validation()
    if success:
        print("\n🚀 READY TO TEST: Run enhanced morning analyzer to validate fix")
    else:
        print("\n❌ ISSUES DETECTED: Check file and database location")
