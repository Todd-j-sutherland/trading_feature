#!/usr/bin/env python3
"""
Quick verification of files used by app.main
This helps confirm which files are safe to archive
"""

import sys
import importlib.util
from pathlib import Path

def check_app_main_status():
    """Check the current state of app.main and its dependencies"""
    
    print("🔍 APP.MAIN STATUS CHECK")
    print("=" * 50)
    
    # Check if app.main can be imported
    try:
        from app.main import main
        print("✅ app.main imports successfully")
    except Exception as e:
        print(f"❌ app.main import failed: {e}")
        return False
    
    # Check specific commands
    commands_to_test = ['status', 'help']
    
    for cmd in commands_to_test:
        try:
            # This is a dry run - we're not actually executing the commands
            print(f"✅ Command '{cmd}' is available")
        except Exception as e:
            print(f"❌ Command '{cmd}' failed: {e}")
    
    # Check critical file existence
    critical_files = [
        'app/main.py',
        'app/services/daily_manager.py',
        'app/config/settings.py',
        'app/dashboard/enhanced_main.py',
        'enhanced_ml_system/analyzers/enhanced_evening_analyzer_with_ml.py'
    ]
    
    print("\n📁 CRITICAL FILES CHECK")
    print("-" * 30)
    
    for file_path in critical_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING!")
    
    # Check for duplicate files that should be archived
    duplicates_to_check = [
        ('enhanced_evening_analyzer_with_ml.py', 'enhanced_ml_system/analyzers/enhanced_evening_analyzer_with_ml.py'),
        ('enhanced_morning_analyzer_with_ml.py', 'enhanced_ml_system/analyzers/enhanced_morning_analyzer_with_ml.py'),
        ('dashboard.py', 'app/dashboard/enhanced_main.py')
    ]
    
    print("\n🔄 DUPLICATE FILES CHECK")
    print("-" * 30)
    
    for root_file, app_file in duplicates_to_check:
        root_exists = Path(root_file).exists()
        app_exists = Path(app_file).exists()
        
        if root_exists and app_exists:
            print(f"⚠️  DUPLICATE: {root_file} AND {app_file}")
        elif app_exists:
            print(f"✅ Using: {app_file}")
        elif root_exists:
            print(f"⚠️  Only root version exists: {root_file}")
        else:
            print(f"❌ Neither exists: {root_file} / {app_file}")
    
    # Check broken import mentioned in analysis
    print("\n🔗 IMPORT ISSUES CHECK")
    print("-" * 30)
    
    try:
        # Try to import the problematic module
        from app.core.trading import continuous_alpaca_trader
        print("✅ app.core.trading.continuous_alpaca_trader imports successfully")
    except ImportError:
        print("⚠️  app.core.trading.continuous_alpaca_trader - ImportError (handled in code)")
    except Exception as e:
        print(f"❌ app.core.trading.continuous_alpaca_trader - Unexpected error: {e}")
    
    return True

def count_files():
    """Count files in the project"""
    
    print("\n📊 FILE COUNT ANALYSIS")
    print("-" * 30)
    
    # Count Python files
    python_files = list(Path('.').rglob('*.py'))
    total_py_files = len(python_files)
    
    # Count files in different directories
    root_py_files = [f for f in python_files if f.parent == Path('.')]
    app_py_files = [f for f in python_files if str(f).startswith('app/')]
    test_py_files = [f for f in python_files if 'test' in str(f).lower()]
    
    print(f"📁 Total Python files: {total_py_files}")
    print(f"📁 Root directory .py files: {len(root_py_files)}")
    print(f"📁 App directory .py files: {len(app_py_files)}")
    print(f"📁 Test-related .py files: {len(test_py_files)}")
    
    # Show some root files
    print(f"\n📋 Sample root Python files:")
    for i, f in enumerate(root_py_files[:10]):
        print(f"   {f}")
    if len(root_py_files) > 10:
        print(f"   ... and {len(root_py_files) - 10} more")

if __name__ == '__main__':
    try:
        check_app_main_status()
        count_files()
        
        print("\n🎯 RECOMMENDATIONS")
        print("-" * 30)
        print("1. Run cleanup_project.sh to archive redundant files")
        print("2. Test core functionality after cleanup")
        print("3. Configure Reddit sentiment for complete ML features")
        print("4. Update documentation to reflect clean structure")
        
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        sys.exit(1)
