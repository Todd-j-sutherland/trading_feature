#!/usr/bin/env python3
"""
Enhanced ML Integration Script
Integrates enhanced ML components into existing trading system

This script:
- Connects enhanced ML pipeline to morning/evening processes
- Updates existing daily_manager to use enhanced predictions
- Provides backward compatibility
- Implements comprehensive testing
"""

import sys
import os
import logging
from datetime import datetime
from typing import Dict, Optional, List

# Setup paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class EnhancedMLIntegrator:
    """Integrates enhanced ML components with existing system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Try to import enhanced components
        try:
            from app.core.ml.enhanced_training_pipeline import EnhancedMLTrainingPipeline
            from enhanced_morning_analyzer_with_ml import EnhancedMorningAnalyzer
            from enhanced_evening_analyzer_with_ml import EnhancedEveningAnalyzer
            self.enhanced_available = True
            
            # Initialize enhanced components
            self.enhanced_pipeline = EnhancedMLTrainingPipeline()
            self.enhanced_morning = EnhancedMorningAnalyzer()
            self.enhanced_evening = EnhancedEveningAnalyzer()
            
            self.logger.info("✅ Enhanced ML components loaded successfully")
            
        except ImportError as e:
            self.logger.warning(f"⚠️ Enhanced ML components not available: {e}")
            self.enhanced_available = False
        
        # Try to import existing components
        try:
            from app.services.daily_manager import DailyManager
            from app.main import TradingSystemManager
            self.existing_available = True
            
            self.daily_manager = DailyManager()
            self.trading_manager = TradingSystemManager()
            
            self.logger.info("✅ Existing system components loaded")
            
        except ImportError as e:
            self.logger.warning(f"⚠️ Existing system components not available: {e}")
            self.existing_available = False
    
    def integrate_enhanced_morning_process(self) -> Dict:
        """Integrate enhanced morning analysis into existing workflow"""
        self.logger.info("🌅 Integrating Enhanced Morning Process")
        
        integration_result = {
            'integration_attempted': True,
            'integration_successful': False,
            'enhanced_analysis': {},
            'fallback_used': False,
            'integration_details': {}
        }
        
        if self.enhanced_available:
            try:
                # Run enhanced morning analysis
                enhanced_result = self.enhanced_morning.run_enhanced_morning_analysis()
                
                if enhanced_result:
                    integration_result['enhanced_analysis'] = enhanced_result
                    integration_result['integration_successful'] = True
                    
                    # Extract key metrics for existing system compatibility
                    integration_result['integration_details'] = {
                        'total_predictions': len(enhanced_result.get('bank_predictions', {})),
                        'avg_confidence': self._calculate_avg_confidence(enhanced_result),
                        'market_sentiment': enhanced_result.get('market_overview', {}).get('overall_sentiment', 'NEUTRAL'),
                        'high_confidence_count': self._count_high_confidence(enhanced_result),
                        'timestamp': enhanced_result.get('timestamp')
                    }
                    
                    self.logger.info("✅ Enhanced morning analysis integrated successfully")
                    
                    # Save integration metadata
                    self._save_integration_metadata('morning', integration_result)
                    
                else:
                    self.logger.warning("⚠️ Enhanced morning analysis returned no results")
                    
            except Exception as e:
                self.logger.error(f"❌ Enhanced morning integration failed: {e}")
                integration_result['error'] = str(e)
        else:
            self.logger.info("🔄 Running fallback morning analysis")
            integration_result['fallback_used'] = True
            
            # Run existing morning process if available
            if self.existing_available:
                try:
                    fallback_result = self.daily_manager.run_morning_analysis()
                    integration_result['enhanced_analysis'] = fallback_result
                    integration_result['integration_successful'] = True
                except Exception as e:
                    self.logger.error(f"❌ Fallback morning analysis failed: {e}")
        
        return integration_result
    
    def integrate_enhanced_evening_process(self) -> Dict:
        """Integrate enhanced evening analysis into existing workflow"""
        self.logger.info("🌆 Integrating Enhanced Evening Process")
        
        integration_result = {
            'integration_attempted': True,
            'integration_successful': False,
            'enhanced_analysis': {},
            'fallback_used': False,
            'integration_details': {}
        }
        
        if self.enhanced_available:
            try:
                # Run enhanced evening analysis
                enhanced_result = self.enhanced_evening.run_enhanced_evening_analysis()
                
                if enhanced_result:
                    integration_result['enhanced_analysis'] = enhanced_result
                    integration_result['integration_successful'] = True
                    
                    # Extract key metrics for existing system compatibility
                    training_result = enhanced_result.get('model_training', {})
                    integration_result['integration_details'] = {
                        'model_trained': training_result.get('training_successful', False),
                        'training_samples': training_result.get('training_data_stats', {}).get('total_samples', 0),
                        'validation_assessment': enhanced_result.get('validation_results', {}).get('overall_assessment', 'UNKNOWN'),
                        'predictions_generated': enhanced_result.get('next_day_predictions', {}).get('predictions_generated', False),
                        'timestamp': enhanced_result.get('timestamp')
                    }
                    
                    self.logger.info("✅ Enhanced evening analysis integrated successfully")
                    
                    # Save integration metadata
                    self._save_integration_metadata('evening', integration_result)
                    
                else:
                    self.logger.warning("⚠️ Enhanced evening analysis returned no results")
                    
            except Exception as e:
                self.logger.error(f"❌ Enhanced evening integration failed: {e}")
                integration_result['error'] = str(e)
        else:
            self.logger.info("🔄 Running fallback evening analysis")
            integration_result['fallback_used'] = True
            
            # Run existing evening process if available
            if self.existing_available:
                try:
                    fallback_result = self.daily_manager.run_evening_analysis()
                    integration_result['enhanced_analysis'] = fallback_result
                    integration_result['integration_successful'] = True
                except Exception as e:
                    self.logger.error(f"❌ Fallback evening analysis failed: {e}")
        
        return integration_result
    
    def validate_enhanced_integration(self) -> Dict:
        """Validate that enhanced components are working correctly"""
        self.logger.info("🔍 Validating Enhanced Integration")
        
        validation_result = {
            'validation_performed': True,
            'components_tested': {},
            'integration_health': 'UNKNOWN',
            'recommendations': []
        }
        
        # Test enhanced pipeline
        if self.enhanced_available:
            validation_result['components_tested']['enhanced_pipeline'] = self._test_enhanced_pipeline()
            validation_result['components_tested']['enhanced_morning'] = self._test_enhanced_morning()
            validation_result['components_tested']['enhanced_evening'] = self._test_enhanced_evening()
        else:
            validation_result['components_tested']['enhanced_pipeline'] = {'available': False}
            validation_result['components_tested']['enhanced_morning'] = {'available': False}
            validation_result['components_tested']['enhanced_evening'] = {'available': False}
        
        # Test existing system compatibility
        if self.existing_available:
            validation_result['components_tested']['existing_system'] = self._test_existing_system()
        else:
            validation_result['components_tested']['existing_system'] = {'available': False}
        
        # Calculate overall health
        working_components = sum(1 for test in validation_result['components_tested'].values() 
                               if test.get('working', False))
        total_components = len(validation_result['components_tested'])
        
        if working_components >= total_components * 0.8:
            validation_result['integration_health'] = 'EXCELLENT'
        elif working_components >= total_components * 0.6:
            validation_result['integration_health'] = 'GOOD'
        elif working_components >= total_components * 0.4:
            validation_result['integration_health'] = 'ACCEPTABLE'
        else:
            validation_result['integration_health'] = 'NEEDS_IMPROVEMENT'
        
        # Generate recommendations
        validation_result['recommendations'] = self._generate_recommendations(validation_result)
        
        return validation_result
    
    def run_full_integration_test(self) -> Dict:
        """Run complete integration test cycle"""
        self.logger.info("🚀 Running Full Integration Test")
        
        test_result = {
            'test_timestamp': datetime.now().isoformat(),
            'morning_integration': {},
            'evening_integration': {},
            'validation_results': {},
            'overall_success': False,
            'summary': {}
        }
        
        # Test morning integration
        self.logger.info("Testing morning integration...")
        test_result['morning_integration'] = self.integrate_enhanced_morning_process()
        
        # Test evening integration
        self.logger.info("Testing evening integration...")
        test_result['evening_integration'] = self.integrate_enhanced_evening_process()
        
        # Validate integration
        self.logger.info("Validating integration...")
        test_result['validation_results'] = self.validate_enhanced_integration()
        
        # Calculate overall success
        morning_success = test_result['morning_integration'].get('integration_successful', False)
        evening_success = test_result['evening_integration'].get('integration_successful', False)
        validation_health = test_result['validation_results'].get('integration_health', 'UNKNOWN')
        
        test_result['overall_success'] = (morning_success and evening_success and 
                                        validation_health in ['EXCELLENT', 'GOOD', 'ACCEPTABLE'])
        
        # Generate summary
        test_result['summary'] = {
            'morning_status': '✅' if morning_success else '❌',
            'evening_status': '✅' if evening_success else '❌',
            'integration_health': validation_health,
            'enhanced_available': self.enhanced_available,
            'existing_available': self.existing_available,
            'fallback_used': (test_result['morning_integration'].get('fallback_used', False) or
                            test_result['evening_integration'].get('fallback_used', False))
        }
        
        self.logger.info(f"Integration test complete: {'✅ SUCCESS' if test_result['overall_success'] else '❌ FAILED'}")
        
        return test_result
    
    def _calculate_avg_confidence(self, analysis_result: Dict) -> float:
        """Calculate average confidence from analysis result"""
        predictions = analysis_result.get('bank_predictions', {})
        if predictions:
            confidences = [pred.get('confidence', 0) for pred in predictions.values()]
            return sum(confidences) / len(confidences) if confidences else 0.0
        return 0.0
    
    def _count_high_confidence(self, analysis_result: Dict) -> int:
        """Count high confidence predictions"""
        predictions = analysis_result.get('bank_predictions', {})
        return sum(1 for pred in predictions.values() if pred.get('confidence', 0) > 0.8)
    
    def _test_enhanced_pipeline(self) -> Dict:
        """Test enhanced ML pipeline"""
        test_result = {'available': True, 'working': False, 'details': {}}
        
        try:
            # Test basic functionality
            test_sentiment = {
                'overall_sentiment': 0.5,
                'confidence': 0.8,
                'news_count': 5,
                'sentiment_components': {},
                'timestamp': datetime.now().isoformat()
            }
            
            prediction = self.enhanced_pipeline.predict_enhanced(test_sentiment, 'CBA.AX')
            
            if 'error' not in prediction:
                test_result['working'] = True
                test_result['details'] = {
                    'prediction_generated': True,
                    'action': prediction.get('optimal_action', 'UNKNOWN'),
                    'confidence': prediction.get('confidence_scores', {}).get('average', 0)
                }
            else:
                test_result['details'] = {'error': prediction['error']}
                
        except Exception as e:
            test_result['details'] = {'error': str(e)}
        
        return test_result
    
    def _test_enhanced_morning(self) -> Dict:
        """Test enhanced morning analyzer"""
        test_result = {'available': True, 'working': False, 'details': {}}
        
        try:
            # Quick test run
            result = self.enhanced_morning.run_enhanced_morning_analysis()
            if result and 'error' not in result:
                test_result['working'] = True
                test_result['details'] = {
                    'analysis_completed': True,
                    'timestamp': result.get('timestamp')
                }
            else:
                test_result['details'] = {'error': result.get('error', 'No result returned')}
                
        except Exception as e:
            test_result['details'] = {'error': str(e)}
        
        return test_result
    
    def _test_enhanced_evening(self) -> Dict:
        """Test enhanced evening analyzer"""
        test_result = {'available': True, 'working': False, 'details': {}}
        
        try:
            # Quick test run
            result = self.enhanced_evening.run_enhanced_evening_analysis()
            if result and 'error' not in result:
                test_result['working'] = True
                test_result['details'] = {
                    'analysis_completed': True,
                    'timestamp': result.get('timestamp')
                }
            else:
                test_result['details'] = {'error': result.get('error', 'No result returned')}
                
        except Exception as e:
            test_result['details'] = {'error': str(e)}
        
        return test_result
    
    def _test_existing_system(self) -> Dict:
        """Test existing system components"""
        test_result = {'available': True, 'working': False, 'details': {}}
        
        try:
            # Test daily manager
            if hasattr(self.daily_manager, 'run_morning_analysis'):
                test_result['working'] = True
                test_result['details'] = {'daily_manager_available': True}
            else:
                test_result['details'] = {'daily_manager_available': False}
                
        except Exception as e:
            test_result['details'] = {'error': str(e)}
        
        return test_result
    
    def _generate_recommendations(self, validation_result: Dict) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        components = validation_result.get('components_tested', {})
        
        # Check enhanced components
        if not components.get('enhanced_pipeline', {}).get('working', False):
            recommendations.append("Install required dependencies for enhanced ML pipeline (pandas, numpy, scikit-learn)")
        
        if not components.get('enhanced_morning', {}).get('working', False):
            recommendations.append("Verify enhanced morning analyzer configuration and data access")
        
        if not components.get('enhanced_evening', {}).get('working', False):
            recommendations.append("Check enhanced evening analyzer database connections and model files")
        
        # Check existing system
        if not components.get('existing_system', {}).get('working', False):
            recommendations.append("Ensure existing trading system components are properly configured")
        
        # Health-specific recommendations
        health = validation_result.get('integration_health', 'UNKNOWN')
        if health == 'NEEDS_IMPROVEMENT':
            recommendations.append("Consider running setup scripts to properly configure all components")
        elif health == 'ACCEPTABLE':
            recommendations.append("Review logs for any configuration warnings or data access issues")
        
        return recommendations
    
    def _save_integration_metadata(self, process_type: str, result: Dict):
        """Save integration metadata for monitoring"""
        try:
            import json
            os.makedirs('data/integration', exist_ok=True)
            
            metadata_file = f'data/integration/{process_type}_integration_{datetime.now().strftime("%Y%m%d")}.json'
            
            with open(metadata_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.warning(f"Failed to save integration metadata: {e}")
    
    def display_integration_summary(self, test_result: Dict):
        """Display comprehensive integration summary"""
        print("\n" + "=" * 80)
        print("🔧 ENHANCED ML INTEGRATION SUMMARY")
        print("=" * 80)
        
        print(f"📅 Test Timestamp: {test_result['test_timestamp']}")
        print(f"🎯 Overall Success: {'✅ YES' if test_result['overall_success'] else '❌ NO'}")
        
        summary = test_result.get('summary', {})
        print(f"\n📊 Component Status:")
        print(f"   Enhanced Components: {'✅ Available' if summary.get('enhanced_available') else '❌ Not Available'}")
        print(f"   Existing System: {'✅ Available' if summary.get('existing_available') else '❌ Not Available'}")
        print(f"   Fallback Used: {'⚠️ Yes' if summary.get('fallback_used') else '✅ No'}")
        
        print(f"\n🌅 Morning Integration:")
        morning = test_result.get('morning_integration', {})
        print(f"   Status: {summary.get('morning_status', '❓')}")
        if morning.get('integration_successful'):
            details = morning.get('integration_details', {})
            print(f"   Predictions: {details.get('total_predictions', 0)}")
            print(f"   Avg Confidence: {details.get('avg_confidence', 0):.3f}")
            print(f"   Market Sentiment: {details.get('market_sentiment', 'UNKNOWN')}")
        
        print(f"\n🌆 Evening Integration:")
        evening = test_result.get('evening_integration', {})
        print(f"   Status: {summary.get('evening_status', '❓')}")
        if evening.get('integration_successful'):
            details = evening.get('integration_details', {})
            print(f"   Model Trained: {'✅' if details.get('model_trained') else '❌'}")
            print(f"   Training Samples: {details.get('training_samples', 0)}")
            print(f"   Validation: {details.get('validation_assessment', 'UNKNOWN')}")
        
        print(f"\n🔍 Validation Results:")
        validation = test_result.get('validation_results', {})
        print(f"   Integration Health: {validation.get('integration_health', 'UNKNOWN')}")
        
        recommendations = validation.get('recommendations', [])
        if recommendations:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        
        print("\n" + "=" * 80)
        
        if test_result['overall_success']:
            print("✅ Enhanced ML integration successful! System ready for use.")
        else:
            print("❌ Integration issues detected. Please review recommendations.")
        
        print("=" * 80)

def main():
    """Main function to run integration"""
    print("🚀 Enhanced ML Integration Script")
    print("Connecting enhanced ML components to existing trading system")
    print("=" * 60)
    
    try:
        # Initialize integrator
        integrator = EnhancedMLIntegrator()
        
        # Run full integration test
        test_result = integrator.run_full_integration_test()
        
        # Display results
        integrator.display_integration_summary(test_result)
        
        return test_result['overall_success']
        
    except KeyboardInterrupt:
        print("\n⚠️ Integration interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
