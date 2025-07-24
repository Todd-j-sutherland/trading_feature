#!/usr/bin/env python3
"""
Comprehensive Unit Test Suite for ML Trading System
Optimized and focused tests for all core components
"""

import unittest
import sys
import os
import logging
from pathlib import Path

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Suppress logging during tests
logging.disable(logging.CRITICAL)

def get_available_test_modules():
    """Dynamically import available test modules"""
    test_modules = []
    test_classes = []
    
    try:
        from tests.test_ml_pipeline import TestMLPipeline
        test_classes.append(TestMLPipeline)
        test_modules.append("test_ml_pipeline")
    except ImportError:
        pass
        
    try:
        from tests.test_data_feed import TestDataFeed
        test_classes.append(TestDataFeed)
        test_modules.append("test_data_feed")
    except ImportError:
        pass
        
    try:
        from tests.test_news_sentiment import TestNewsSentiment
        test_classes.append(TestNewsSentiment)
        test_modules.append("test_news_sentiment")
    except ImportError:
        pass
        
    try:
        from tests.test_trading_analyzer import TestTradingAnalyzer
        test_classes.append(TestTradingAnalyzer)
        test_modules.append("test_trading_analyzer")
    except ImportError:
        pass
        
    try:
        from tests.test_daily_manager import TestDailyManager
        test_classes.append(TestDailyManager)
        test_modules.append("test_daily_manager")
    except ImportError:
        pass
        
    try:
        from tests.test_comprehensive_analyzer import TestComprehensiveAnalyzer
        test_classes.append(TestComprehensiveAnalyzer)
        test_modules.append("test_comprehensive_analyzer")
    except ImportError:
        pass
        
    try:
        from tests.test_system_integration import TestSystemIntegration
        test_classes.append(TestSystemIntegration)
        test_modules.append("test_system_integration")
    except ImportError:
        pass
    
    return test_classes, test_modules

def run_test_suite():
    """Run the complete test suite"""
    print("🧪 ML Trading System - Comprehensive Unit Tests")
    print("=" * 60)
    
    # Get available test modules
    test_classes, test_modules = get_available_test_modules()
    
    if not test_classes:
        print("❌ No test modules found!")
        print("💡 Make sure test files exist in the tests/ directory")
        return False
    
    print(f"📋 Found {len(test_classes)} test modules:")
    for module in test_modules:
        print(f"   ✓ {module}")
    
    print(f"\n🚀 Running tests...")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "="*60)
    print("🧪 TEST SUITE SUMMARY")
    print("="*60)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\n🚨 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED!")
        return True
    else:
        print("\n❌ SOME TESTS FAILED!")
        return False

def run_quick_tests():
    """Run a quick subset of critical tests"""
    print("🚀 Running Quick Test Suite...")
    
    # Get available test modules
    test_classes, test_modules = get_available_test_modules()
    
    if not test_classes:
        print("❌ No test modules found for quick tests!")
        return False
    
    # Only run the first few most important tests from each available module
    quick_suite = unittest.TestSuite()
    
    for test_class in test_classes[:3]:  # Only first 3 modules
        # Add just one representative test from each class
        try:
            test_methods = [method for method in dir(test_class) 
                          if method.startswith('test_') and 'initialization' in method]
            if test_methods:
                quick_suite.addTest(test_class(test_methods[0]))
            else:
                # Fallback to any test method
                all_methods = [method for method in dir(test_class) 
                             if method.startswith('test_')]
                if all_methods:
                    quick_suite.addTest(test_class(all_methods[0]))
        except Exception as e:
            print(f"⚠️ Could not add tests from {test_class.__name__}: {e}")
    
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(quick_suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ML Trading System Test Suite")
    parser.add_argument("--quick", action="store_true", help="Run quick test subset")
    parser.add_argument("--component", type=str, help="Test specific component")
    parser.add_argument("--list", action="store_true", help="List available test modules")
    
    args = parser.parse_args()
    
    # Get available test modules for dynamic component mapping
    test_classes, test_modules = get_available_test_modules()
    component_map = {}
    
    for i, test_class in enumerate(test_classes):
        module_name = test_modules[i] if i < len(test_modules) else test_class.__name__
        # Create simple component names
        if 'ml_pipeline' in module_name:
            component_map['ml'] = test_class
        elif 'data_feed' in module_name:
            component_map['data'] = test_class
        elif 'news_sentiment' in module_name:
            component_map['sentiment'] = test_class
        elif 'trading_analyzer' in module_name:
            component_map['analyzer'] = test_class
        elif 'daily_manager' in module_name:
            component_map['manager'] = test_class
        elif 'comprehensive' in module_name:
            component_map['comprehensive'] = test_class
        elif 'integration' in module_name:
            component_map['integration'] = test_class
    
    if args.list:
        print("📋 Available test components:")
        for name in component_map.keys():
            print(f"   {name}")
        sys.exit(0)
    
    if args.quick:
        success = run_quick_tests()
    elif args.component:
        if args.component in component_map:
            print(f"🔍 Testing component: {args.component}")
            suite = unittest.TestLoader().loadTestsFromTestCase(component_map[args.component])
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)
            success = result.wasSuccessful()
        else:
            print(f"❌ Unknown component: {args.component}")
            print(f"Available: {', '.join(component_map.keys())}")
            success = False
    else:
        success = run_test_suite()
    
    sys.exit(0 if success else 1)
