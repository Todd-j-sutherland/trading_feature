#!/usr/bin/env python3
"""
Test Integration with app.main Commands
Demonstrates how the enhanced ML components work with app.main morning/evening
"""

import os
import sys
import logging
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_morning_integration():
    """Test enhanced morning analysis integration"""
    print("\n🌅 TESTING MORNING ANALYSIS INTEGRATION")
    print("=" * 60)
    
    try:
        # Import the daily manager which orchestrates morning/evening routines
        from app.services.daily_manager import TradingSystemManager
        
        # Initialize the manager
        manager = TradingSystemManager()
        
        # Test morning routine
        print("Running morning routine with enhanced ML integration...")
        result = manager.morning_routine()
        
        if result:
            print("✅ Morning routine completed successfully")
            print(f"   Trading system manager available")
        else:
            print("❌ Morning routine failed")
        
        return result
        
    except Exception as e:
        print(f"❌ Morning integration test failed: {e}")
        return False

def test_evening_integration():
    """Test enhanced evening analysis integration"""
    print("\n🌆 TESTING EVENING ANALYSIS INTEGRATION")
    print("=" * 60)
    
    try:
        # Import the daily manager
        from app.services.daily_manager import TradingSystemManager
        
        # Initialize the manager
        manager = TradingSystemManager()
        
        # Test evening routine
        print("Running evening routine with enhanced ML integration...")
        result = manager.evening_routine()
        
        if result:
            print("✅ Evening routine completed successfully")
            print(f"   Trading system manager available")
        else:
            print("❌ Evening routine failed")
        
        return result
        
    except Exception as e:
        print(f"❌ Evening integration test failed: {e}")
        return False

def test_enhanced_component_detection():
    """Test that enhanced ML components are properly detected"""
    print("\n🔍 TESTING ENHANCED COMPONENT DETECTION")
    print("=" * 60)
    
    detection_results = {
        'enhanced_morning_analyzer': False,
        'enhanced_evening_analyzer': False,
        'enhanced_ml_pipeline': False
    }
    
    # Test enhanced morning analyzer
    try:
        from enhanced_ml_system.analyzers.enhanced_morning_analyzer_with_ml import EnhancedMorningAnalyzer
        detection_results['enhanced_morning_analyzer'] = True
        print("✅ Enhanced Morning Analyzer: Available")
    except ImportError:
        print("❌ Enhanced Morning Analyzer: Not available")
    
    # Test enhanced evening analyzer
    try:
        from enhanced_ml_system.analyzers.enhanced_evening_analyzer_with_ml import EnhancedEveningAnalyzer
        detection_results['enhanced_evening_analyzer'] = True
        print("✅ Enhanced Evening Analyzer: Available")
    except ImportError:
        print("❌ Enhanced Evening Analyzer: Not available")
    
    # Test enhanced ML pipeline
    try:
        from app.core.ml.enhanced_training_pipeline import EnhancedMLTrainingPipeline
        detection_results['enhanced_ml_pipeline'] = True
        print("✅ Enhanced ML Pipeline: Available")
    except ImportError:
        print("❌ Enhanced ML Pipeline: Not available")
    
    print(f"\nDetection Summary: {sum(detection_results.values())}/3 enhanced components available")
    return detection_results

def test_feature_extraction_capabilities():
    """Test that feature extraction works with real symbols"""
    print("\n⚙️ TESTING FEATURE EXTRACTION CAPABILITIES")
    print("=" * 60)
    
    try:
        from enhanced_ml_system.analyzers.enhanced_morning_analyzer_with_ml import EnhancedMorningAnalyzer
        
        analyzer = EnhancedMorningAnalyzer()
        
        # Test with CBA.AX
        print("Testing enhanced morning analysis for CBA.AX...")
        result = analyzer.run_enhanced_morning_analysis()
        
        if result.get('success'):
            analysis_results = result.get('analysis_results', {})
            
            print(f"✅ Enhanced morning analysis successful")
            print(f"   Analysis results available: {'Yes' if analysis_results else 'No'}")
            print(f"   Symbols analyzed: {len(analysis_results.get('individual_analysis', {}))}")
            
            # Show enhanced features if available
            if 'enhanced_features' in result:
                features = result['enhanced_features']
                print(f"   Enhanced features extracted: {len(features)}")
            
            return True
        else:
            print(f"❌ Enhanced morning analysis failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Feature extraction test failed: {e}")
        return False

def main():
    """Main function to run all integration tests"""
    print("🧪 APP.MAIN INTEGRATION TEST SUITE")
    print("=" * 80)
    print("Testing enhanced ML integration with app.main morning/evening commands")
    print("=" * 80)
    
    test_results = {
        'component_detection': False,
        'feature_extraction': False,
        'morning_integration': False,
        'evening_integration': False
    }
    
    # Test 1: Component Detection
    detection_results = test_enhanced_component_detection()
    test_results['component_detection'] = sum(detection_results.values()) >= 2
    
    # Test 2: Feature Extraction (if components available)
    if detection_results['enhanced_morning_analyzer']:
        test_results['feature_extraction'] = test_feature_extraction_capabilities()
    else:
        print("\n⚠️ Skipping feature extraction test - Enhanced Morning Analyzer not available")
    
    # Test 3: Morning Integration
    test_results['morning_integration'] = test_morning_integration()
    
    # Test 4: Evening Integration  
    test_results['evening_integration'] = test_evening_integration()
    
    # Final Results
    print("\n📊 FINAL TEST RESULTS")
    print("=" * 60)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name.replace('_', ' ').title()}: {status}")
    
    success_rate = passed_tests / total_tests
    print(f"\nOverall Success Rate: {passed_tests}/{total_tests} ({success_rate:.1%})")
    
    if success_rate >= 0.75:
        print("🎉 App.main integration: EXCELLENT")
        assessment = "EXCELLENT"
    elif success_rate >= 0.5:
        print("✅ App.main integration: GOOD")
        assessment = "GOOD"
    else:
        print("❌ App.main integration: NEEDS IMPROVEMENT")
        assessment = "NEEDS_IMPROVEMENT"
    
    # Create summary
    summary = {
        'test_timestamp': datetime.now().isoformat(),
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'success_rate': success_rate,
        'assessment': assessment,
        'test_results': test_results,
        'component_detection': detection_results
    }
    
    # Save results
    import json
    results_file = f"data/app_main_integration_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs('data', exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    return success_rate >= 0.5

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
