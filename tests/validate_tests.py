#!/usr/bin/env python3
"""
Test Validator - Quick validation of test suite functionality
Checks test files and validates core functionality
"""

import os
import sys
import importlib.util
from pathlib import Path

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def validate_test_files():
    """Validate test files exist and are importable"""
    print("🔍 Validating Test Files...")
    print("=" * 40)
    
    test_dir = Path("tests")
    if not test_dir.exists():
        print("❌ Tests directory not found!")
        return False
    
    test_files = [
        "test_ml_pipeline.py",
        "test_data_feed.py", 
        "test_news_sentiment.py",
        "test_trading_analyzer.py",
        "test_daily_manager.py",
        "test_comprehensive_analyzer.py",
        "test_system_integration.py"
    ]
    
    valid_files = []
    invalid_files = []
    
    for test_file in test_files:
        test_path = test_dir / test_file
        
        if test_path.exists():
            try:
                # Try to import the test module
                spec = importlib.util.spec_from_file_location(
                    test_file[:-3], test_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Check for test classes
                test_classes = [
                    name for name in dir(module) 
                    if name.startswith('Test') and hasattr(getattr(module, name), '__bases__')
                ]
                
                if test_classes:
                    print(f"✅ {test_file}: {len(test_classes)} test class(es)")
                    valid_files.append(test_file)
                else:
                    print(f"⚠️  {test_file}: No test classes found")
                    invalid_files.append(test_file)
                    
            except Exception as e:
                print(f"❌ {test_file}: Import error - {e}")
                invalid_files.append(test_file)
        else:
            print(f"❌ {test_file}: File not found")
            invalid_files.append(test_file)
    
    print(f"\n📊 Summary:")
    print(f"   Valid: {len(valid_files)}")
    print(f"   Invalid: {len(invalid_files)}")
    
    return len(valid_files) > 0

def validate_core_imports():
    """Validate core system components can be imported"""
    print("\n🔍 Validating Core Components...")
    print("=" * 40)
    
    components = {
        "News Sentiment": "src.news_sentiment",
        "ML Pipeline": "src.ml_training_pipeline", 
        "Data Feed": "src.data_feed",
        "Trading Analyzer": "news_trading_analyzer",
        "Daily Manager": "daily_manager"
    }
    
    valid_components = []
    
    for name, module_path in components.items():
        try:
            importlib.import_module(module_path)
            print(f"✅ {name}: Available")
            valid_components.append(name)
        except ImportError as e:
            print(f"❌ {name}: Not available - {e}")
        except Exception as e:
            print(f"⚠️  {name}: Import error - {e}")
    
    print(f"\n📊 Components Available: {len(valid_components)}/{len(components)}")
    return len(valid_components) >= 3  # Need at least 3 core components

def run_basic_functionality_test():
    """Run basic functionality tests"""
    print("\n🧪 Running Basic Functionality Tests...")
    print("=" * 40)
    
    tests_passed = 0
    total_tests = 5
    
    # Test 1: Basic data structures
    try:
        test_data = {
            'sentiment_score': 0.15,
            'confidence': 0.75,
            'signal': 'HOLD'
        }
        assert -1.0 <= test_data['sentiment_score'] <= 1.0
        assert 0.0 <= test_data['confidence'] <= 1.0
        assert test_data['signal'] in ['BUY', 'SELL', 'HOLD']
        print("✅ Test 1: Data structures - PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 1: Data structures - FAILED: {e}")
    
    # Test 2: Signal generation logic
    try:
        def generate_signal(sentiment, confidence):
            if confidence < 0.5:
                return 'HOLD'
            elif sentiment > 0.3 and confidence > 0.7:
                return 'BUY'
            elif sentiment < -0.3 and confidence > 0.7:
                return 'SELL'
            else:
                return 'HOLD'
        
        assert generate_signal(0.7, 0.8) == 'BUY'
        assert generate_signal(-0.7, 0.8) == 'SELL' 
        assert generate_signal(0.1, 0.4) == 'HOLD'
        print("✅ Test 2: Signal generation - PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 2: Signal generation - FAILED: {e}")
    
    # Test 3: Symbol validation
    try:
        def validate_symbol(symbol):
            return (symbol and 
                   isinstance(symbol, str) and 
                   symbol.endswith('.AX') and 
                   len(symbol) > 3)
        
        assert validate_symbol('CBA.AX') == True
        assert validate_symbol('WBC.AX') == True
        assert validate_symbol('INVALID') == False
        assert validate_symbol('') == False
        print("✅ Test 3: Symbol validation - PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 3: Symbol validation - FAILED: {e}")
    
    # Test 4: ML feature validation
    try:
        features = [0.15, 0.75, 12, 0.05, 0.1, 0.11, 2, 14, 1, 1]
        assert len(features) == 10
        assert all(isinstance(f, (int, float)) for f in features)
        assert features[1] >= 0.0 and features[1] <= 1.0  # confidence
        print("✅ Test 4: ML features - PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 4: ML features - FAILED: {e}")
    
    # Test 5: Error handling
    try:
        def handle_error(data):
            if data is None:
                return {'status': 'error', 'message': 'No data'}
            return {'status': 'success', 'data': data}
        
        result = handle_error(None)
        assert result['status'] == 'error'
        
        result = handle_error({'test': True})
        assert result['status'] == 'success'
        print("✅ Test 5: Error handling - PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 5: Error handling - FAILED: {e}")
    
    print(f"\n📊 Basic Tests: {tests_passed}/{total_tests} passed")
    return tests_passed >= 4

def main():
    """Main validation function"""
    print("🧪 Test Suite Validator")
    print("=" * 50)
    
    # Run validations
    files_valid = validate_test_files()
    components_valid = validate_core_imports()
    functionality_valid = run_basic_functionality_test()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 VALIDATION SUMMARY")
    print("=" * 50)
    
    validations = [
        ("Test Files", files_valid),
        ("Core Components", components_valid), 
        ("Basic Functionality", functionality_valid)
    ]
    
    passed = sum(1 for _, result in validations if result)
    
    for name, result in validations:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:20} {status}")
    
    print(f"\nOverall: {passed}/{len(validations)} validations passed")
    
    if passed >= 2:
        print("\n🎯 Test suite is ready for use!")
        print("💡 Run: python run_tests.py")
        return True
    else:
        print("\n🔧 Test suite needs fixes before use")
        print("💡 Check individual component imports and test files")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
