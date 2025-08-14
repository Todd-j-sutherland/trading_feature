"""
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
