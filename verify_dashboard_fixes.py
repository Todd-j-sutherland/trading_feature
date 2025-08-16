#!/usr/bin/env python3
"""
Verify that all dashboard fixes are in place
"""
import ast
import sys

def check_file_fixes():
    """Check if all necessary fixes are present in the dashboard file"""
    
    with open('comprehensive_table_dashboard.py', 'r') as f:
        content = f.read()
    
    fixes_status = {}
    
    # Check 1: analysis_results initialization in __init__
    if 'self.analysis_results = {}' in content:
        fixes_status['init_analysis_results'] = '✅ PRESENT'
    else:
        fixes_status['init_analysis_results'] = '❌ MISSING'
    
    # Check 2: Path conversion in __init__
    if 'self.root_dir = Path(root_dir)' in content:
        fixes_status['path_conversion'] = '✅ PRESENT'
    else:
        fixes_status['path_conversion'] = '❌ MISSING'
    
    # Check 3: Proper boolean check for analysis_results
    if 'if self.analysis_results is not None' in content:
        fixes_status['boolean_check'] = '✅ PRESENT'
    else:
        fixes_status['boolean_check'] = '❌ MISSING'
    
    # Check 4: load_analysis_results method exists
    if 'def load_analysis_results(self):' in content:
        fixes_status['load_method'] = '✅ PRESENT'
    else:
        fixes_status['load_method'] = '❌ MISSING'
    
    print("🔍 Dashboard Fixes Verification:")
    print("=" * 50)
    
    all_good = True
    for fix, status in fixes_status.items():
        print(f"{fix:25} : {status}")
        if '❌' in status:
            all_good = False
    
    print("=" * 50)
    
    if all_good:
        print("🚀 ALL FIXES PRESENT - File ready for remote deployment!")
        return True
    else:
        print("⚠️  MISSING FIXES - File needs updates before remote deployment!")
        return False

if __name__ == "__main__":
    success = check_file_fixes()
    sys.exit(0 if success else 1)
