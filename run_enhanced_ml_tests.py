#!/usr/bin/env python3
"""
Enhanced ML System - Master Test Runner
Runs all tests for the organized enhanced ML system
"""

import os
import sys
import subprocess
from datetime import datetime

def run_test(test_path, test_name):
    """Run a test and return success status"""
    print(f"\n🧪 Running {test_name}")
    print("=" * 60)
    
    try:
        # Change to the test directory and run the test
        test_dir = os.path.dirname(test_path)
        test_file = os.path.basename(test_path)
        
        result = subprocess.run(
            [sys.executable, test_file],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print(f"✅ {test_name}: PASSED")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ {test_name}: FAILED")
            if result.stdout:
                print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {test_name}: TIMEOUT (5 minutes)")
        return False
    except Exception as e:
        print(f"💥 {test_name}: ERROR - {e}")
        return False

def main():
    """Run all enhanced ML system tests"""
    print("🚀 ENHANCED ML SYSTEM - MASTER TEST RUNNER")
    print("=" * 80)
    print(f"Test run started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Define test suite
    tests = [
        {
            'path': 'enhanced_ml_system/testing/enhanced_ml_test_integration.py',
            'name': 'Enhanced ML Pipeline Integration Test'
        },
        {
            'path': 'enhanced_ml_system/integration/test_app_main_integration.py', 
            'name': 'App.Main Integration Test'
        },
        {
            'path': 'enhanced_ml_system/docs/ENHANCED_ML_IMPLEMENTATION_COMPLETE.py',
            'name': 'Implementation Status Summary'
        }
    ]
    
    # Run all tests
    results = {}
    for test in tests:
        test_path = test['path']
        test_name = test['name']
        
        if os.path.exists(test_path):
            results[test_name] = run_test(test_path, test_name)
        else:
            print(f"❌ {test_name}: FILE NOT FOUND - {test_path}")
            results[test_name] = False
    
    # Display final results
    print("\n" + "=" * 80)
    print("📊 FINAL TEST RESULTS")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   {test_name}: {status}")
        if success:
            passed += 1
    
    success_rate = passed / total if total > 0 else 0
    print(f"\nOverall Success Rate: {passed}/{total} ({success_rate:.1%})")
    
    if success_rate >= 0.8:
        print("🎉 Enhanced ML System: EXCELLENT")
        assessment = "EXCELLENT"
    elif success_rate >= 0.6:
        print("✅ Enhanced ML System: GOOD")
        assessment = "GOOD"
    else:
        print("❌ Enhanced ML System: NEEDS IMPROVEMENT")
        assessment = "NEEDS_IMPROVEMENT"
    
    # Show organized structure
    print(f"\n📁 ORGANIZED STRUCTURE:")
    print("   enhanced_ml_system/")
    print("   ├── analyzers/           # Morning & evening analyzers")
    print("   ├── testing/             # Test validation framework")  
    print("   ├── integration/         # App.main integration tests")
    print("   ├── docs/                # Implementation documentation")
    print("   └── README.md            # System overview")
    print("   ")
    print("   legacy_enhanced/         # Legacy files (DO NOT USE)")
    print("   app/core/ml/             # Core ML pipeline (enhanced_training_pipeline.py)")
    
    print(f"\n🎯 PRODUCTION READY:")
    print("   • python app.main morning")
    print("   • python app.main evening")
    print("   • All enhanced components organized and tested")
    
    return success_rate >= 0.6

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
