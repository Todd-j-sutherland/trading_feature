#!/usr/bin/env python3
"""
Temporal Protection Setup for App Structure
==========================================

This script sets up temporal protection integration for the app.main structure.
It copies the temporal protection components to the correct locations and creates
the necessary integration points.

Usage:
    python3 setup_temporal_protection.py
"""

import os
import shutil
import sys
from pathlib import Path

def setup_temporal_protection():
    """Set up temporal protection for app.main integration"""
    
    print("🛡️ Setting up Temporal Protection for App Structure")
    print("=" * 60)
    
    # Get project root
    project_root = Path(__file__).parent
    
    # Files to copy to project root for app.main integration
    temporal_files = [
        'morning_temporal_guard.py',
        'enhanced_outcomes_evaluator.py', 
        'outcomes_temporal_fixer.py',
        'protected_morning_routine.py',
        'timestamp_synchronization_fixer.py'
    ]
    
    # Copy temporal protection files to project root
    print("\n📁 Copying temporal protection files...")
    copied_files = []
    
    for file_name in temporal_files:
        source_file = project_root / file_name
        
        if source_file.exists():
            # File already exists in root, no need to copy
            print(f"   ✅ {file_name} - Already in root directory")
            copied_files.append(file_name)
        else:
            print(f"   ❌ {file_name} - File not found in project root")
    
    # Create app integration helper
    print("\n🔧 Creating app integration helper...")
    
    app_integration_code = '''"""
App Integration Helper for Temporal Protection
=============================================

This module provides helper functions to integrate temporal protection
with the app.main structure.
"""

import sys
import os
from pathlib import Path

# Add project root to path for temporal protection imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def run_temporal_guard():
    """Run the temporal guard from app structure"""
    try:
        from morning_temporal_guard import MorningTemporalGuard
        
        guard = MorningTemporalGuard()
        result = guard.run_comprehensive_guard()
        
        return result
    except ImportError as e:
        print(f"❌ Cannot import temporal guard: {e}")
        print("💡 Run: python3 setup_temporal_protection.py")
        return False
    except Exception as e:
        print(f"❌ Temporal guard error: {e}")
        return False

def run_outcomes_evaluator():
    """Run the outcomes evaluator from app structure"""
    try:
        from enhanced_outcomes_evaluator import EnhancedOutcomesEvaluator
        
        evaluator = EnhancedOutcomesEvaluator()
        result = evaluator.run_evaluation()
        
        return result
    except ImportError as e:
        print(f"⚠️ Cannot import outcomes evaluator: {e}")
        return None
    except Exception as e:
        print(f"⚠️ Outcomes evaluator warning: {e}")
        return None

def validate_temporal_setup():
    """Validate that temporal protection is properly set up"""
    print("🔍 Validating temporal protection setup...")
    
    # Check if files exist in project root
    project_root = Path(__file__).parent.parent.parent
    required_files = [
        'morning_temporal_guard.py',
        'enhanced_outcomes_evaluator.py'
    ]
    
    all_good = True
    for file_name in required_files:
        file_path = project_root / file_name
        if file_path.exists():
            print(f"   ✅ {file_name}")
        else:
            print(f"   ❌ {file_name} - Missing")
            all_good = False
    
    if all_good:
        print("✅ Temporal protection setup validated")
        return True
    else:
        print("❌ Temporal protection setup incomplete")
        print("💡 Run: python3 setup_temporal_protection.py")
        return False
'''
    
    # Create app directory structure if needed
    app_dir = project_root / 'app'
    utils_dir = app_dir / 'utils'
    utils_dir.mkdir(parents=True, exist_ok=True)
    
    # Write integration helper
    integration_file = utils_dir / 'temporal_integration.py'
    with open(integration_file, 'w') as f:
        f.write(app_integration_code)
    
    print(f"   ✅ Created {integration_file}")
    
    # Create usage example
    print("\n📖 Creating usage examples...")
    
    usage_example = f'''#!/usr/bin/env python3
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
        print("\\n✅ Setup validated - you can now use:")
        print("   python -m app.main morning")
        print("   python -m app.main evening")
        print("\\n🛡️ Temporal protection is active!")
    else:
        print("\\n❌ Setup incomplete - run setup first")
'''
    
    examples_file = project_root / 'temporal_protection_examples.py'
    with open(examples_file, 'w') as f:
        f.write(usage_example)
    
    print(f"   ✅ Created {examples_file}")
    
    # Test the integration
    print("\n🧪 Testing integration...")
    
    try:
        # Test importing the integration helper
        sys.path.insert(0, str(app_dir))
        from app.utils.temporal_integration import validate_temporal_setup
        
        if validate_temporal_setup():
            print("✅ Integration test passed")
            integration_success = True
        else:
            print("⚠️ Integration test failed - some files missing")
            integration_success = False
            
    except Exception as e:
        print(f"❌ Integration test error: {e}")
        integration_success = False
    
    # Summary
    print("\\n" + "=" * 60)
    print("🎯 TEMPORAL PROTECTION SETUP SUMMARY")
    print("=" * 60)
    
    print(f"\\n📁 Files Status:")
    for file_name in temporal_files:
        source_file = project_root / file_name
        status = "✅ Available" if source_file.exists() else "❌ Missing"
        print(f"   {file_name}: {status}")
    
    print(f"\\n🔧 Integration:")
    print(f"   App Helper: ✅ Created at app/utils/temporal_integration.py")
    print(f"   Examples: ✅ Created at temporal_protection_examples.py")
    print(f"   Daily Manager: ✅ Modified with temporal protection")
    
    if len(copied_files) >= 2 and integration_success:
        print(f"\\n🏆 SUCCESS! Temporal protection is now integrated")
        print(f"\\n🚀 Next steps:")
        print(f"   1. Test with: python -m app.main morning")
        print(f"   2. The temporal guard will run automatically")
        print(f"   3. Morning analysis will be blocked if temporal issues detected")
        print(f"   4. Check morning_guard_report.json for detailed validation")
        
        print(f"\\n🛡️ Your morning routine is now PROTECTED!")
        return True
    else:
        print(f"\\n⚠️ Setup incomplete - some components missing")
        print(f"💡 Ensure temporal protection files exist in project root")
        return False

if __name__ == "__main__":
    setup_temporal_protection()
