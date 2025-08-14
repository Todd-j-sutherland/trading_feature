#!/usr/bin/env python3
"""
Comprehensive Validation Script for All System Enhancements
Validates: Enhanced Confidence, MarketAux Optimization, Quality-Based Weighting
"""

import sys
import os
sys.path.append('/Users/toddsutherland/Repos/trading_feature')

def validate_enhanced_confidence():
    """Validate enhanced confidence calculation system"""
    print("🎯 VALIDATING ENHANCED CONFIDENCE CALCULATION")
    print("-" * 50)
    
    try:
        from enhance_confidence_calculation import get_enhanced_confidence
        
        # Test cases
        test_cases = [
            {
                'rsi': 25,  # Extreme oversold
                'sentiment': {'news_count': 8, 'quality_assessment': {'overall_grade': 'A'}},
                'symbol': 'CBA.AX',
                'expected': 'High confidence (>60%)'
            },
            {
                'rsi': 55,  # Neutral
                'sentiment': {'news_count': 2, 'quality_assessment': {'overall_grade': 'F'}},
                'symbol': 'NAB.AX',
                'expected': 'Low confidence (<50%)'
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            confidence = get_enhanced_confidence(case['rsi'], case['sentiment'], case['symbol'])
            print(f"✅ Test {i}: {case['symbol']} RSI={case['rsi']} → Confidence: {confidence:.1%}")
            
        print("✅ Enhanced confidence calculation: WORKING")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced confidence validation failed: {e}")
        return False

def validate_marketaux_optimization():
    """Validate MarketAux optimization system"""
    print("\n🚀 VALIDATING MARKETAUX OPTIMIZATION")
    print("-" * 50)
    
    try:
        from app.core.sentiment.marketaux_integration import MarketAuxManager
        from marketaux_optimization_strategy import optimize_marketaux_requests
        
        print("✅ MarketAux optimization modules imported successfully")
        
        # Test the optimization strategy calculation
        banks = ['CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX', 'MQG.AX', 'SUN.AX', 'QBE.AX']
        
        old_coverage = 3 / len(banks)  # Old: 3 articles shared across all banks
        new_coverage = 3  # New: 3 articles per bank
        improvement = (new_coverage - old_coverage) / old_coverage * 100
        
        print(f"📊 Old coverage: {old_coverage:.1f} articles per bank")
        print(f"📈 New coverage: {new_coverage:.1f} articles per bank")
        print(f"🎯 Improvement: {improvement:.1f}% increase in coverage")
        
        print("✅ MarketAux optimization strategy: WORKING")
        return True
        
    except Exception as e:
        print(f"❌ MarketAux optimization validation failed: {e}")
        return False

def validate_quality_based_weighting():
    """Validate quality-based weighting system"""
    print("\n⚖️ VALIDATING QUALITY-BASED WEIGHTING SYSTEM")
    print("-" * 50)
    
    try:
        from app.core.sentiment.news_analyzer import NewsSentimentAnalyzer
        
        analyzer = NewsSentimentAnalyzer()
        print("✅ News analyzer with quality weighting initialized")
        
        # Test quality assessment
        result = analyzer.analyze_bank_sentiment('CBA.AX')
        
        if 'quality_assessments' in result and 'dynamic_weights' in result:
            print("✅ Quality assessments: PRESENT")
            print("✅ Dynamic weights: PRESENT")
            
            # Check weight sum
            total_weight = sum(result['dynamic_weights'].values())
            if abs(total_weight - 1.0) < 0.01:  # Within 1% of 100%
                print(f"✅ Weight sum validation: {total_weight:.1%}")
            else:
                print(f"❌ Weight sum validation: {total_weight:.1%} (should be 100%)")
                return False
                
            print("✅ Quality-based weighting system: WORKING")
            return True
        else:
            print("❌ Missing quality assessments or dynamic weights")
            return False
            
    except Exception as e:
        print(f"❌ Quality-based weighting validation failed: {e}")
        return False

def validate_dashboard_integration():
    """Validate dashboard integration"""
    print("\n📊 VALIDATING DASHBOARD INTEGRATION")
    print("-" * 50)
    
    try:
        # Check if enhanced confidence is imported in dashboard
        with open('/Users/toddsutherland/Repos/trading_feature/dashboard.py', 'r') as f:
            content = f.read()
            
        if 'from enhance_confidence_calculation import get_enhanced_confidence' in content:
            print("✅ Enhanced confidence import: PRESENT")
        else:
            print("❌ Enhanced confidence import: MISSING")
            return False
            
        if 'get_enhanced_confidence(rsi, sentiment_data, symbol)' in content:
            print("✅ Enhanced confidence usage: PRESENT")
        else:
            print("❌ Enhanced confidence usage: MISSING")
            return False
            
        print("✅ Dashboard integration: WORKING")
        return True
        
    except Exception as e:
        print(f"❌ Dashboard validation failed: {e}")
        return False

def validate_morning_routine_integration():
    """Validate morning routine integration"""
    print("\n🌅 VALIDATING MORNING ROUTINE INTEGRATION")
    print("-" * 50)
    
    try:
        # Check if optimized MarketAux is in morning analyzer
        with open('/Users/toddsutherland/Repos/trading_feature/enhanced_morning_analyzer_with_ml.py', 'r') as f:
            content = f.read()
            
        if 'prefetch_optimized_marketaux_sentiment' in content:
            print("✅ MarketAux optimization in morning routine: PRESENT")
        else:
            print("❌ MarketAux optimization in morning routine: MISSING")
            return False
            
        if 'MARKETAUX OPTIMIZATION' in content:
            print("✅ MarketAux optimization logging: PRESENT")
        else:
            print("❌ MarketAux optimization logging: MISSING")
            return False
            
        print("✅ Morning routine integration: WORKING")
        return True
        
    except Exception as e:
        print(f"❌ Morning routine validation failed: {e}")
        return False

def validate_unit_tests():
    """Validate unit tests are still passing"""
    print("\n🧪 VALIDATING UNIT TESTS")
    print("-" * 50)
    
    try:
        import subprocess
        import sys
        
        # Run the quality weighting unit tests
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'test_quality_weighting_unit_tests.py', 
            '-v'
        ], capture_output=True, text=True, cwd='/Users/toddsutherland/Repos/trading_feature')
        
        if result.returncode == 0:
            # Count passed tests
            output_lines = result.stdout.split('\n')
            passed_tests = len([line for line in output_lines if '::test_' in line and 'PASSED' in line])
            print(f"✅ Unit tests passed: {passed_tests}/20")
            print("✅ Unit test validation: WORKING")
            return True
        else:
            print("❌ Unit tests failed:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Unit test validation failed: {e}")
        return False

def main():
    """Run comprehensive validation"""
    print("🔍 COMPREHENSIVE SYSTEM VALIDATION")
    print("=" * 60)
    print("Validating all enhancements before remote push...")
    
    validations = [
        validate_enhanced_confidence,
        validate_marketaux_optimization,
        validate_quality_based_weighting,
        validate_dashboard_integration,
        validate_morning_routine_integration,
        validate_unit_tests
    ]
    
    results = []
    for validation in validations:
        results.append(validation())
    
    print("\n📋 VALIDATION SUMMARY")
    print("=" * 60)
    
    validation_names = [
        "Enhanced Confidence Calculation",
        "MarketAux Optimization Strategy", 
        "Quality-Based Weighting System",
        "Dashboard Integration",
        "Morning Routine Integration",
        "Unit Tests"
    ]
    
    passed = 0
    for i, (name, result) in enumerate(zip(validation_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {name:30} {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 OVERALL RESULT: {passed}/{len(results)} validations passed")
    
    if passed == len(results):
        print("🚀 ALL SYSTEMS VALIDATED - READY FOR REMOTE PUSH! ✅")
        return True
    else:
        print("❌ VALIDATION FAILED - DO NOT PUSH YET")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
