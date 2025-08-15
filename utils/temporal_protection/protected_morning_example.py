#!/usr/bin/env python3
"""
Protected Morning Analysis Example

This shows how to integrate temporal protection into your existing morning routine.
"""

import sys
from morning_temporal_guard import MorningTemporalGuard

def main():
    # Step 1: ALWAYS run temporal guard first
    guard = MorningTemporalGuard()
    
    print("🛡️  Running temporal integrity guard...")
    is_safe = guard.run_comprehensive_guard()
    
    if not is_safe:
        print("🛑 ABORTING: Temporal integrity issues detected")
        print("🔧 Run timestamp_synchronization_fixer.py to fix issues")
        sys.exit(1)
    
    # Step 2: Only proceed if guard passes
    print("\n✅ Temporal guard passed - proceeding with analysis")
    
    # Your existing morning analysis code goes here
    # For example:
    # from enhanced_morning_analyzer_with_ml import run_morning_analysis
    # run_morning_analysis()
    
    print("🏆 Protected morning analysis completed successfully!")

if __name__ == "__main__":
    main()
