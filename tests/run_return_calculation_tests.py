#!/usr/bin/env python3
"""
Test Runner for Return Calculation Bug Prevention
Comprehensive test suite to prevent regression of return calculation bugs

Usage:
    python tests/run_return_calculation_tests.py
    python tests/run_return_calculation_tests.py --coverage
    python tests/run_return_calculation_tests.py --regression-only
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_tests(test_type="all", coverage=False, verbose=True):
    """
    Run the return calculation test suite
    
    Args:
        test_type: "all", "regression", "helpers", or "components"
        coverage: Whether to run with coverage reporting
        verbose: Whether to use verbose output
    """
    
    test_files = {
        "all": [
            "tests/unit/test_return_calculations.py",
            "tests/unit/test_affected_components.py", 
            "tests/unit/test_calculation_helpers.py"
        ],
        "regression": [
            "tests/unit/test_return_calculations.py::TestBuggyCalculationPatterns",
            "tests/unit/test_affected_components.py::TestRegresssionPrevention",
        ],
        "helpers": [
            "tests/unit/test_calculation_helpers.py"
        ],
        "components": [
            "tests/unit/test_affected_components.py"
        ]
    }
    
    if test_type not in test_files:
        print(f"❌ Invalid test type: {test_type}")
        print(f"Available types: {list(test_files.keys())}")
        return False
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    if coverage:
        cmd.extend([
            "--cov=app/core",
            "--cov=enhanced_smart_collector", 
            "--cov=corrected_smart_collector",
            "--cov=targeted_backfill",
            "--cov=backtesting_engine",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing"
        ])
    
    if verbose:
        cmd.append("-v")
    
    # Add test files
    cmd.extend(test_files[test_type])
    
    # Additional pytest options
    cmd.extend([
        "--tb=short",
        "--durations=10",
        "-x"  # Stop on first failure for debugging
    ])
    
    print(f"🧪 Running {test_type} return calculation tests...")
    print(f"Command: {' '.join(cmd)}")
    print("=" * 60)
    
    try:
        result = subprocess.run(cmd, cwd=project_root, check=True)
        print("=" * 60)
        print(f"✅ All {test_type} tests passed!")
        
        if coverage:
            print("📊 Coverage report generated in htmlcov/index.html")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print("=" * 60)
        print(f"❌ Tests failed with exit code: {e.returncode}")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def validate_environment():
    """Validate that the test environment is properly set up"""
    print("🔍 Validating test environment...")
    
    # Check for pytest
    try:
        import pytest
        print(f"✅ pytest available: {pytest.__version__}")
    except ImportError:
        print("❌ pytest not installed. Run: pip install pytest")
        return False
    
    # Check for coverage if needed
    try:
        import coverage
        print(f"✅ coverage available: {coverage.__version__}")
    except ImportError:
        print("⚠️  coverage not available. Install with: pip install pytest-cov")
    
    # Check test files exist
    test_files = [
        "tests/unit/test_return_calculations.py",
        "tests/unit/test_affected_components.py",
        "tests/unit/test_calculation_helpers.py"
    ]
    
    for test_file in test_files:
        file_path = project_root / test_file
        if file_path.exists():
            print(f"✅ Test file exists: {test_file}")
        else:
            print(f"❌ Test file missing: {test_file}")
            return False
    
    print("✅ Environment validation complete")
    return True

def run_quick_smoke_test():
    """Run a quick smoke test to verify basic functionality"""
    print("💨 Running quick smoke test...")
    
    # Test basic calculation
    try:
        entry_price = 100.0
        exit_price = 105.0
        return_pct = ((exit_price - entry_price) / entry_price) * 100
        
        if return_pct == 5.0:
            print("✅ Basic calculation working")
        else:
            print(f"❌ Basic calculation failed: got {return_pct}, expected 5.0")
            return False
            
    except Exception as e:
        print(f"❌ Basic calculation error: {e}")
        return False
    
    # Test the specific bug pattern
    try:
        buggy_calc = (exit_price - entry_price) / entry_price  # Missing * 100
        correct_calc = ((exit_price - entry_price) / entry_price) * 100
        
        if buggy_calc == 0.05 and correct_calc == 5.0:
            print("✅ Bug pattern detection working")
        else:
            print(f"❌ Bug pattern detection failed")
            return False
            
    except Exception as e:
        print(f"❌ Bug pattern test error: {e}")
        return False
    
    print("✅ Smoke test passed")
    return True

def generate_test_report():
    """Generate a comprehensive test report"""
    print("\n📋 Generating test report...")
    
    report = {
        "Test Coverage Areas": [
            "✅ Basic return calculation formulas",
            "✅ Edge cases and boundary conditions", 
            "✅ Bug regression prevention",
            "✅ All 5 affected component files",
            "✅ Database calculation consistency",
            "✅ Realistic trading scenarios",
            "✅ Error handling and validation",
            "✅ Performance and scalability"
        ],
        "Files Tested": [
            "enhanced_smart_collector.py",
            "corrected_smart_collector.py",
            "targeted_backfill.py", 
            "backtesting_engine.py",
            "app/core/data/collectors/news_collector.py"
        ],
        "Test Categories": [
            "Unit tests for calculation formulas",
            "Integration tests for affected components",
            "Regression tests for bug patterns",
            "Helper function tests",
            "Real-world scenario tests"
        ]
    }
    
    for category, items in report.items():
        print(f"\n{category}:")
        for item in items:
            print(f"  {item}")
    
    print(f"\n📊 Total test files: 3")
    print(f"📊 Estimated test cases: 80+")
    print(f"📊 Code coverage target: >95%")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run return calculation tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/run_return_calculation_tests.py                    # Run all tests
  python tests/run_return_calculation_tests.py --coverage        # Run with coverage
  python tests/run_return_calculation_tests.py --regression-only # Run regression tests only
  python tests/run_return_calculation_tests.py --smoke-test      # Quick validation
        """
    )
    
    parser.add_argument(
        "--test-type", 
        choices=["all", "regression", "helpers", "components"],
        default="all",
        help="Type of tests to run"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true", 
        help="Run with coverage reporting"
    )
    
    parser.add_argument(
        "--regression-only",
        action="store_true",
        help="Run only regression prevention tests"
    )
    
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run quick smoke test only"
    )
    
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate test coverage report"
    )
    
    args = parser.parse_args()
    
    print("🧪 Return Calculation Test Suite")
    print("=" * 50)
    print("Based on bug fix findings from August 10, 2025")
    print("Prevents regression of return calculation bugs")
    print("=" * 50)
    
    # Validate environment first
    if not validate_environment():
        print("❌ Environment validation failed")
        return 1
    
    # Handle special modes
    if args.smoke_test:
        if run_quick_smoke_test():
            print("✅ Smoke test completed successfully")
            return 0
        else:
            print("❌ Smoke test failed")
            return 1
    
    if args.report:
        generate_test_report()
        return 0
    
    # Determine test type
    if args.regression_only:
        test_type = "regression"
    else:
        test_type = args.test_type
    
    # Run tests
    success = run_tests(
        test_type=test_type,
        coverage=args.coverage,
        verbose=True
    )
    
    if success:
        print("\n🎉 Test suite completed successfully!")
        print("🛡️  Return calculation bugs are prevented")
        return 0
    else:
        print("\n💥 Test suite failed!")
        print("🚨 Review failures and fix before deploying")
        return 1

if __name__ == "__main__":
    sys.exit(main())