#!/usr/bin/env python3
"""
Protected Morning Routine Wrapper

This wrapper ensures your morning routine always runs with temporal integrity protection.
It runs the temporal guard FIRST, and only proceeds with analysis if all checks pass.

Usage:
    python3 protected_morning_routine.py [your_morning_script.py]

Example:
    python3 protected_morning_routine.py enhanced_morning_analyzer_with_ml.py
"""

import sys
import subprocess
from datetime import datetime
from pathlib import Path

class ProtectedMorningRoutine:
    """Wrapper that enforces temporal integrity before morning analysis"""
    
    def __init__(self, morning_script: str = None):
        self.morning_script = morning_script
        self.guard_script = "morning_temporal_guard.py"
        
    def run_temporal_guard(self) -> bool:
        """Run the temporal integrity guard"""
        
        print("🛡️  RUNNING TEMPORAL INTEGRITY GUARD...")
        print("=" * 50)
        
        try:
            # Run the guard
            result = subprocess.run([
                sys.executable, self.guard_script
            ], capture_output=True, text=True)
            
            # Print guard output
            print(result.stdout)
            
            if result.stderr:
                print("Guard errors:")
                print(result.stderr)
            
            # Return whether guard passed (exit code 0)
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Error running temporal guard: {e}")
            return False
    
    def run_morning_analysis(self) -> bool:
        """Run the actual morning analysis script"""
        
        if not self.morning_script:
            print("⚠️  No morning script specified - guard validation only")
            return True
        
        script_path = Path(self.morning_script)
        if not script_path.exists():
            print(f"❌ Morning script not found: {self.morning_script}")
            return False
        
        print(f"\n🌅 RUNNING PROTECTED MORNING ANALYSIS...")
        print(f"📄 Script: {self.morning_script}")
        print("=" * 50)
        
        try:
            # Run the morning analysis
            result = subprocess.run([
                sys.executable, str(script_path)
            ], capture_output=False, text=True)  # Show output in real-time
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Error running morning analysis: {e}")
            return False
    
    def run_protected_routine(self) -> int:
        """Run the complete protected morning routine"""
        
        start_time = datetime.now()
        
        print("🌅 PROTECTED MORNING ROUTINE")
        print("=" * 60)
        print(f"🕐 Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if self.morning_script:
            print(f"📄 Morning script: {self.morning_script}")
        
        # Step 1: Run temporal guard
        print("\n📍 STEP 1: TEMPORAL INTEGRITY VALIDATION")
        guard_passed = self.run_temporal_guard()
        
        if not guard_passed:
            print("\n🛑 MORNING ROUTINE ABORTED")
            print("🚨 Temporal integrity guard failed")
            print("🔧 Fix the issues identified by the guard before proceeding")
            print("\n💡 Common fixes:")
            print("  • Run timestamp_synchronization_fixer.py")
            print("  • Check for data leakage issues")
            print("  • Verify technical indicator calculations")
            print("  • Ensure ML models are functioning")
            return 1
        
        # Step 2: Run morning analysis (if specified)
        if self.morning_script:
            print("\n📍 STEP 2: MORNING ANALYSIS")
            analysis_success = self.run_morning_analysis()
            
            if not analysis_success:
                print("\n⚠️  MORNING ANALYSIS COMPLETED WITH ERRORS")
                print("📋 Check the analysis output above for details")
                return 2
        
        # Step 3: Success summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "=" * 60)
        print("🏆 PROTECTED MORNING ROUTINE COMPLETED SUCCESSFULLY")
        print(f"✅ Temporal integrity validated")
        
        if self.morning_script:
            print(f"✅ Morning analysis completed")
        
        print(f"🕐 Duration: {duration:.1f} seconds")
        print(f"📄 Guard report: morning_guard_report.json")
        print("=" * 60)
        
        return 0

def main():
    """Main function for protected morning routine"""
    
    # Get morning script from command line arguments
    morning_script = None
    if len(sys.argv) > 1:
        morning_script = sys.argv[1]
    
    # Run protected routine
    routine = ProtectedMorningRoutine(morning_script)
    exit_code = routine.run_protected_routine()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
