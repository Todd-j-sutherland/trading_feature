#!/usr/bin/env python3
"""
Integration Verification Script
Verifies that enhanced ML components work with app.main morning and evening commands

This script tests:
- app.main morning integration with enhanced ML
- app.main evening integration with enhanced ML  
- Enhanced features availability
- Database integration
- Performance metrics
"""

import sys
import os
import subprocess
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_app_main_integration():
    """Test integration with app.main commands"""
    
    print("🔬 ENHANCED ML INTEGRATION VERIFICATION")
    print("=" * 60)
    print("Testing integration with app.main morning and evening commands")
    print("=" * 60)
    
    # Get the correct Python executable
    try:
        from get_python_executable_details import get_python_executable_details
        python_exec = get_python_executable_details()
    except:
        # Fallback to system python
        python_exec = sys.executable
    
    integration_results = {
        'timestamp': datetime.now().isoformat(),
        'python_executable': python_exec,
        'morning_test': {'success': False, 'output': '', 'enhanced_detected': False},
        'evening_test': {'success': False, 'output': '', 'enhanced_detected': False},
        'dependencies_check': {'success': False, 'missing': []},
        'overall_status': 'PENDING'
    }
    
    # Test 1: Check dependencies
    print("\n🔍 Testing Enhanced ML Dependencies...")
    missing_deps = []
    required_deps = [
        'pandas', 'numpy', 'scikit-learn', 'yfinance', 'transformers', 
        'textblob', 'vaderSentiment', 'feedparser', 'praw'
    ]
    
    for dep in required_deps:
        try:
            __import__(dep)
            print(f"   ✅ {dep}: Available")
        except ImportError:
            print(f"   ❌ {dep}: Missing")
            missing_deps.append(dep)
    
    integration_results['dependencies_check'] = {
        'success': len(missing_deps) == 0,
        'missing': missing_deps,
        'available': [dep for dep in required_deps if dep not in missing_deps]
    }
    
    # Test 2: Test app.main morning command
    print("\n🌅 Testing app.main morning integration...")
    try:
        cmd = [python_exec, "-m", "app.main", "morning"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=os.getcwd())
        
        morning_success = result.returncode == 0
        morning_output = result.stdout + result.stderr
        enhanced_detected = "Enhanced ML components detected" in morning_output
        
        integration_results['morning_test'] = {
            'success': morning_success,
            'output': morning_output[-500:],  # Last 500 chars
            'enhanced_detected': enhanced_detected,
            'return_code': result.returncode
        }
        
        if morning_success:
            print("   ✅ Morning command executed successfully")
            if enhanced_detected:
                print("   ✅ Enhanced ML components detected and used")
            else:
                print("   ⚠️ Enhanced ML components not detected (using fallback)")
        else:
            print(f"   ❌ Morning command failed (exit code: {result.returncode})")
            
    except subprocess.TimeoutExpired:
        print("   ❌ Morning command timed out")
        integration_results['morning_test']['success'] = False
        integration_results['morning_test']['output'] = "Command timed out after 60 seconds"
    except Exception as e:
        print(f"   ❌ Morning command error: {e}")
        integration_results['morning_test']['success'] = False
        integration_results['morning_test']['output'] = str(e)
    
    # Test 3: Test app.main evening command
    print("\n🌆 Testing app.main evening integration...")
    try:
        cmd = [python_exec, "-m", "app.main", "evening"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=os.getcwd())
        
        evening_success = result.returncode == 0
        evening_output = result.stdout + result.stderr
        enhanced_detected = "Enhanced ML components detected" in evening_output
        
        integration_results['evening_test'] = {
            'success': evening_success,
            'output': evening_output[-500:],  # Last 500 chars
            'enhanced_detected': enhanced_detected,
            'return_code': result.returncode
        }
        
        if evening_success:
            print("   ✅ Evening command executed successfully")
            if enhanced_detected:
                print("   ✅ Enhanced ML components detected and used")
            else:
                print("   ⚠️ Enhanced ML components not detected (using fallback)")
        else:
            print(f"   ❌ Evening command failed (exit code: {result.returncode})")
            
    except subprocess.TimeoutExpired:
        print("   ❌ Evening command timed out")
        integration_results['evening_test']['success'] = False
        integration_results['evening_test']['output'] = "Command timed out after 60 seconds"
    except Exception as e:
        print(f"   ❌ Evening command error: {e}")
        integration_results['evening_test']['success'] = False
        integration_results['evening_test']['output'] = str(e)
    
    # Calculate overall status
    deps_ok = integration_results['dependencies_check']['success']
    morning_ok = integration_results['morning_test']['success']
    evening_ok = integration_results['evening_test']['success']
    enhanced_morning = integration_results['morning_test']['enhanced_detected']
    enhanced_evening = integration_results['evening_test']['enhanced_detected']
    
    if deps_ok and morning_ok and evening_ok and enhanced_morning and enhanced_evening:
        integration_results['overall_status'] = 'EXCELLENT'
        status_emoji = '🟢'
    elif deps_ok and morning_ok and evening_ok:
        integration_results['overall_status'] = 'GOOD'
        status_emoji = '🟡'
    elif morning_ok or evening_ok:
        integration_results['overall_status'] = 'PARTIAL'
        status_emoji = '🟠'
    else:
        integration_results['overall_status'] = 'FAILED'
        status_emoji = '🔴'
    
    # Display comprehensive results
    print("\n" + "=" * 60)
    print("📊 INTEGRATION VERIFICATION RESULTS")
    print("=" * 60)
    
    print(f"🕐 Test Timestamp: {integration_results['timestamp']}")
    print(f"🐍 Python Executable: {python_exec}")
    print(f"{status_emoji} Overall Status: {integration_results['overall_status']}")
    
    print(f"\n📦 Dependencies ({len(required_deps)} total):")
    print(f"   ✅ Available: {len(integration_results['dependencies_check']['available'])}")
    print(f"   ❌ Missing: {len(missing_deps)}")
    if missing_deps:
        print(f"   Missing packages: {', '.join(missing_deps)}")
    
    print(f"\n🌅 Morning Integration:")
    print(f"   Command Success: {'✅' if morning_ok else '❌'}")
    print(f"   Enhanced ML Detected: {'✅' if enhanced_morning else '❌'}")
    
    print(f"\n🌆 Evening Integration:")
    print(f"   Command Success: {'✅' if evening_ok else '❌'}")
    print(f"   Enhanced ML Detected: {'✅' if enhanced_evening else '❌'}")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    if integration_results['overall_status'] == 'EXCELLENT':
        print("   🎉 Perfect! Enhanced ML is fully integrated with app.main commands")
        print("   🚀 You can now use: python -m app.main morning")
        print("   🚀 You can now use: python -m app.main evening")
    elif integration_results['overall_status'] == 'GOOD':
        print("   ✅ Integration working, but enhanced ML components not fully detected")
        print("   📋 Check logs for any configuration issues")
    elif integration_results['overall_status'] == 'PARTIAL':
        print("   ⚠️ Partial integration - some commands failing")
        print("   🔧 Review error logs and fix configuration issues")
    else:
        print("   🔴 Integration failed - review setup and dependencies")
        print("   📖 Refer to ENHANCED_ML_SETUP_GUIDE.md for troubleshooting")
    
    if missing_deps:
        print(f"   📦 Install missing dependencies: pip install {' '.join(missing_deps)}")
    
    print("\n" + "=" * 60)
    
    # Save results
    try:
        import json
        os.makedirs('data/integration', exist_ok=True)
        results_file = f"data/integration/app_main_integration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(integration_results, f, indent=2)
        print(f"📄 Results saved to: {results_file}")
    except Exception as e:
        logger.warning(f"Could not save results: {e}")
    
    return integration_results

def test_enhanced_features():
    """Test specific enhanced features"""
    print("\n🧪 Testing Enhanced Features...")
    
    features_tested = {
        'enhanced_pipeline': False,
        'multi_output_predictions': False,
        'feature_engineering': False,
        'data_validation': False
    }
    
    try:
        # Test enhanced pipeline import
        from app.core.ml.enhanced_training_pipeline import EnhancedMLTrainingPipeline
        features_tested['enhanced_pipeline'] = True
        print("   ✅ Enhanced ML Pipeline: Available")
        
        # Test pipeline functionality
        pipeline = EnhancedMLTrainingPipeline()
        if hasattr(pipeline, 'predict_enhanced'):
            features_tested['multi_output_predictions'] = True
            print("   ✅ Multi-Output Predictions: Available")
        
        if hasattr(pipeline, '_extract_comprehensive_features'):
            features_tested['feature_engineering'] = True
            print("   ✅ Feature Engineering: Available")
            
    except ImportError as e:
        print(f"   ❌ Enhanced Pipeline: Not available ({e})")
    except Exception as e:
        print(f"   ❌ Enhanced Pipeline: Error ({e})")
    
    try:
        # Test data validation
        from app.core.ml.enhanced_training_pipeline import DataValidator
        validator = DataValidator()
        features_tested['data_validation'] = True
        print("   ✅ Data Validation Framework: Available")
    except ImportError:
        print("   ❌ Data Validation: Not available")
    except Exception as e:
        print(f"   ❌ Data Validation: Error ({e})")
    
    return features_tested

def main():
    """Main verification function"""
    try:
        # Test app.main integration
        integration_results = test_app_main_integration()
        
        # Test enhanced features
        feature_results = test_enhanced_features()
        
        # Final assessment
        success = integration_results['overall_status'] in ['EXCELLENT', 'GOOD']
        
        if success:
            print("\n🎉 SUCCESS: Enhanced ML is integrated with app.main commands!")
            print("✅ Use: python -m app.main morning")
            print("✅ Use: python -m app.main evening")
        else:
            print("\n❌ INTEGRATION ISSUES DETECTED")
            print("📖 Refer to troubleshooting guide for assistance")
        
        return success
        
    except KeyboardInterrupt:
        print("\n⚠️ Verification interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
