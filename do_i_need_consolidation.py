#!/usr/bin/env python3
"""
Consolidation Decision Script
Quick check to determine if database consolidation is needed
"""

import subprocess
import sys

def check_consolidation_need():
    """
    Determine if consolidation is needed based on your specific situation
    """
    print("🤔 DO YOU NEED DATABASE CONSOLIDATION?")
    print("=" * 50)
    
    print("📊 YOUR SITUATION:")
    print("   • Morning routine shows: 'Banks Analyzed: 7, Feature Pipeline: 371 features'")
    print("   • Database query shows: 'Features: 187, Outcomes: 10'")
    print("   • Discrepancy: 371 ≠ 187 features")
    
    print(f"\n🎯 DECISION LOGIC:")
    
    # Check 1: Data discrepancy
    morning_features = 371
    database_features = 187
    discrepancy = morning_features - database_features
    
    print(f"   1. Feature count discrepancy: {discrepancy} features")
    if discrepancy > 50:
        print("      → ✅ YES, significant discrepancy detected")
        need_consolidation = True
    else:
        print("      → ❌ NO, minimal discrepancy")
        need_consolidation = False
    
    # Check 2: Outcomes sufficiency
    database_outcomes = 10
    print(f"   2. Outcomes count: {database_outcomes}")
    if database_outcomes < 50:
        print("      → ⚠️ INSUFFICIENT for ML training")
        need_outcomes = True
    else:
        print("      → ✅ SUFFICIENT for ML training")
        need_outcomes = False
    
    # Check 3: Multiple database likelihood
    print(f"   3. Multiple database files likely: ✅ YES")
    print("      → Evidence: Different feature counts suggest separate databases")
    
    print(f"\n🎯 RECOMMENDATION:")
    
    if need_consolidation:
        print("   ✅ YES, YOU NEED CONSOLIDATION")
        print("   📋 Reasons:")
        print(f"     • {discrepancy} missing features in main database")
        print("     • Morning routine and database query show different data")
        print("     • Likely multiple database files with scattered data")
        
        print(f"\n💡 SOLUTION STEPS:")
        print("   1. Run on remote server:")
        print("      ssh root@170.64.199.151")
        print("      cd /root/test && source ../trading_venv/bin/activate")
        print("   2. Upload and run:")
        print("      python3 fix_database_consolidation.py")
        print("   3. Verify fix:")
        print("      python3 -c \"[database check command]\"")
        
        print(f"\n🎉 EXPECTED RESULT:")
        print("   • Database features: 187 → 371+ (matching morning routine)")
        print("   • Outcomes: 10 → 50+ (ML training ready)")
        print("   • No synthetic data needed - all real market data!")
        
    else:
        print("   ❌ NO, CONSOLIDATION NOT NEEDED")
        print("   💡 Alternative solutions:")
        print("     • Check database paths and working directories")
        print("     • Verify morning routine is writing to correct database")
        print("     • Look for transaction commit issues")
    
    return need_consolidation

def create_remote_command():
    """
    Create the exact command to run on remote server
    """
    print(f"\n📋 EXACT REMOTE COMMANDS:")
    print("Copy and paste these commands on your remote server:")
    
    print(f"\n# 1. Connect and setup")
    print("ssh root@170.64.199.151")
    print("cd /root/test && source ../trading_venv/bin/activate")
    
    print(f"\n# 2. Quick check current state")
    print('python3 -c "import sqlite3; conn = sqlite3.connect(\\"data/ml_models/enhanced_training_data.db\\"); cursor = conn.cursor(); cursor.execute(\\"SELECT COUNT(*) FROM enhanced_features\\"); features = cursor.fetchone()[0]; cursor.execute(\\"SELECT COUNT(*) FROM enhanced_outcomes WHERE price_direction_1h IS NOT NULL\\"); outcomes = cursor.fetchone()[0]; print(f\\"Before: Features={features}, Outcomes={outcomes}\\"); conn.close()"')
    
    print(f"\n# 3. Run consolidation (if needed)")
    print("python3 fix_database_consolidation.py")
    
    print(f"\n# 4. Verify fix")
    print('python3 -c "import sqlite3; conn = sqlite3.connect(\\"data/ml_models/enhanced_training_data.db\\"); cursor = conn.cursor(); cursor.execute(\\"SELECT COUNT(*) FROM enhanced_features\\"); features = cursor.fetchone()[0]; cursor.execute(\\"SELECT COUNT(*) FROM enhanced_outcomes WHERE price_direction_1h IS NOT NULL\\"); outcomes = cursor.fetchone()[0]; print(f\\"After: Features={features}, Outcomes={outcomes}\\"); print(f\\"Training ready: {\\\\\\"✅ YES\\\\\\" if features >= 50 and outcomes >= 50 else \\\\\\"❌ NO\\\\\\"}\\"); conn.close()"')
    
    print(f"\n# 5. Test morning routine")
    print("python -m app.main morning")

if __name__ == "__main__":
    need_consolidation = check_consolidation_need()
    
    if need_consolidation:
        create_remote_command()
    
    print(f"\n" + "=" * 50)
    if need_consolidation:
        print("🎯 ANSWER: YES, run database consolidation")
    else:
        print("🎯 ANSWER: NO, investigate other causes")
    print("=" * 50)
