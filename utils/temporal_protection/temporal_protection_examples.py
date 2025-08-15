#!/usr/bin/env python3
"""
Usage Examples for Temporal Protection with App Structure
========================================================

Examples of how to use temporal protection with python -m app.main morning
"""

# Example 1: Direct integration in daily_manager.py (already implemented)
# The morning_routine() method now includes temporal guard validation

# Example 2: Manual validation before analysis
def validate_before_analysis():
    from app.utils.temporal_integration import run_temporal_guard
    
    if not run_temporal_guard():
        print("❌ Temporal integrity failed - aborting analysis")
        return False
    
    print("✅ Temporal integrity validated - proceeding with analysis")
    return True

# Example 3: Evening outcomes evaluation  
def evening_outcomes_cleanup():
    from app.utils.temporal_integration import run_outcomes_evaluator
    
    result = run_outcomes_evaluator()
    if result:
        print("✅ Outcomes evaluation completed")
    else:
        print("⚠️ Outcomes evaluation had issues")

# Example 4: Setup validation
def check_setup():
    from app.utils.temporal_integration import validate_temporal_setup
    
    return validate_temporal_setup()

if __name__ == "__main__":
    print("🛡️ Temporal Protection Usage Examples")
    print("=" * 50)
    
    # Validate setup
    if check_setup():
        print("\n✅ Setup validated - you can now use:")
        print("   python -m app.main morning")
        print("   python -m app.main evening")
        print("\n🛡️ Temporal protection is active!")
    else:
        print("\n❌ Setup incomplete - run setup first")
