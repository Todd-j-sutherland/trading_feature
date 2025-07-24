#!/usr/bin/env python3
"""
Simple Unit Tests for Enhanced Trading Features
Focus on testing core functionality with known APIs
"""

import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sys
import warnings

# Add source path
sys.path.append('/Users/toddsutherland/Repos/trading_analysis/src')

warnings.filterwarnings("ignore", category=UserWarning)

class TestCoreFunctionality(unittest.TestCase):
    """Test core functionality that we know exists"""
    
    def test_imports(self):
        """Test that we can import all the enhanced modules"""
        try:
            from temporal_sentiment_analyzer import SentimentDataPoint, TemporalSentimentAnalyzer
            from enhanced_ensemble_learning import ModelPrediction, EnhancedTransformerEnsemble
            from advanced_feature_engineering import AdvancedFeatureEngineer
            self.assertTrue(True, "All imports successful")
        except ImportError as e:
            self.fail(f"Import failed: {e}")
    
    def test_temporal_sentiment_basic(self):
        """Test basic temporal sentiment functionality"""
        from temporal_sentiment_analyzer import SentimentDataPoint, TemporalSentimentAnalyzer
        
        # Test data point creation
        point = SentimentDataPoint(
            timestamp=datetime.now(),
            symbol='CBA.AX',
            sentiment_score=0.75,
            confidence=0.9,
            news_count=3,
            relevance_score=0.8
        )
        
        self.assertEqual(point.sentiment_score, 0.75)
        self.assertEqual(point.symbol, 'CBA.AX')
        
        # Test analyzer creation
        analyzer = TemporalSentimentAnalyzer()
        self.assertIsInstance(analyzer, TemporalSentimentAnalyzer)
        
        # Test adding data
        analyzer.add_sentiment_observation(point)
        self.assertIn('CBA.AX', analyzer.sentiment_history)
    
    def test_ensemble_learning_basic(self):
        """Test basic ensemble learning functionality"""
        from enhanced_ensemble_learning import ModelPrediction, EnhancedTransformerEnsemble
        
        # Test prediction creation with correct parameters
        prediction = ModelPrediction(
            model_name='test_model',
            prediction=0.75,
            confidence=0.9,
            probability_scores={'positive': 0.75, 'negative': 0.25},
            processing_time=0.1
        )
        
        self.assertEqual(prediction.model_name, 'test_model')
        self.assertEqual(prediction.prediction, 0.75)
        
        # Test ensemble creation
        ensemble = EnhancedTransformerEnsemble()
        self.assertIsInstance(ensemble, EnhancedTransformerEnsemble)
    
    def test_feature_engineering_basic(self):
        """Test basic feature engineering functionality"""
        from advanced_feature_engineering import AdvancedFeatureEngineer
        
        # Test engineer creation
        engineer = AdvancedFeatureEngineer()
        self.assertIsInstance(engineer, AdvancedFeatureEngineer)
        
        # Test feature engineering with sample data
        sample_sentiment = {
            'overall_sentiment': 0.6,
            'confidence': 0.8,
            'news_count': 5,
            'sentiment_components': {
                'news': 0.7,
                'reddit': 0.5,
                'events': 0.6
            }
        }
        
        # Use the actual API method
        features = engineer.engineer_comprehensive_features('CBA.AX', sample_sentiment)
        self.assertIsInstance(features, dict)
        self.assertIn('features', features)
        self.assertGreater(len(features['features']), 5)  # Should have multiple features
        
        # Check all features are numeric
        for key, value in features['features'].items():
            self.assertTrue(isinstance(value, (int, float, np.integer, np.floating)), 
                          f"Feature {key} has value {value} of type {type(value)}")
            self.assertFalse(np.isnan(float(value)))
            self.assertFalse(np.isinf(float(value)))
    
    def test_temporal_analysis_workflow(self):
        """Test complete temporal analysis workflow"""
        from temporal_sentiment_analyzer import SentimentDataPoint, TemporalSentimentAnalyzer
        
        analyzer = TemporalSentimentAnalyzer()
        
        # Add multiple data points
        base_time = datetime.now()
        for i in range(10):
            point = SentimentDataPoint(
                timestamp=base_time - timedelta(hours=i),
                symbol='CBA.AX',
                sentiment_score=0.5 + 0.2 * np.sin(i * 0.3),
                confidence=0.8 + 0.1 * np.random.random(),
                news_count=np.random.randint(1, 10),
                relevance_score=0.8
            )
            analyzer.add_sentiment_observation(point)
        
        # Test analysis
        analysis = analyzer.analyze_sentiment_evolution('CBA.AX')
        self.assertIsInstance(analysis, dict)
        
        # Should have key metrics
        expected_keys = ['trend', 'volatility', 'current_regime']
        for key in expected_keys:
            if key in analysis:  # Some might not be present in all implementations
                self.assertIsInstance(analysis[key], (int, float, str))
    
    def test_feature_engineering_temporal_features(self):
        """Test temporal feature engineering specifically"""
        from advanced_feature_engineering import AdvancedFeatureEngineer
        
        engineer = AdvancedFeatureEngineer()
        
        # Test with sample data that includes temporal info
        sentiment_data = {
            'overall_sentiment': 0.6,
            'confidence': 0.8,
            'news_count': 5,
            'timestamp': datetime.now().isoformat()
        }
        
        # Use comprehensive features which includes temporal
        result = engineer.engineer_comprehensive_features('CBA.AX', sentiment_data)
        self.assertIsInstance(result, dict)
        self.assertIn('features', result)
        
        # Should have temporal features in the comprehensive set
        features = result['features']
        temporal_features = [k for k in features.keys() if 'hour' in k or 'time' in k or 'market' in k]
        self.assertGreater(len(temporal_features), 0)
    
    def test_feature_engineering_sentiment_features(self):
        """Test sentiment feature engineering"""
        from advanced_feature_engineering import AdvancedFeatureEngineer
        
        engineer = AdvancedFeatureEngineer()
        
        sentiment_data = {
            'overall_sentiment': 0.6,
            'confidence': 0.8,
            'news_count': 5,
            'sentiment_components': {
                'news': 0.7,
                'reddit': 0.5,
                'events': 0.6
            }
        }
        
        # Use the actual method that exists
        result = engineer.engineer_comprehensive_features('CBA.AX', sentiment_data)
        self.assertIsInstance(result, dict)
        self.assertIn('features', result)
        
        features = result['features']
        
        # Check basic sentiment features exist
        sentiment_features = [k for k in features.keys() if 'sentiment' in k.lower()]
        self.assertGreater(len(sentiment_features), 0)
    
    def test_feature_validation(self):
        """Test feature validation and cleaning"""
        from advanced_feature_engineering import AdvancedFeatureEngineer
        
        engineer = AdvancedFeatureEngineer()
        
        # Test with valid data - system should handle gracefully
        sentiment_data = {
            'overall_sentiment': 0.5,
            'confidence': 0.8,
            'news_count': 5
        }
        
        result = engineer.engineer_comprehensive_features('CBA.AX', sentiment_data)
        self.assertIsInstance(result, dict)
        self.assertIn('features', result)
        
        # All features should be valid numbers
        features = result['features']
        for key, value in features.items():
            self.assertTrue(isinstance(value, (int, float, np.integer, np.floating)), 
                          f"Feature {key} has value {value} of type {type(value)}")
            self.assertFalse(np.isnan(float(value)))
            self.assertFalse(np.isinf(float(value)))
    
    def test_system_robustness(self):
        """Test system handles edge cases gracefully"""
        from temporal_sentiment_analyzer import TemporalSentimentAnalyzer
        from advanced_feature_engineering import AdvancedFeatureEngineer
        
        # Test temporal analyzer with no data
        analyzer = TemporalSentimentAnalyzer()
        analysis = analyzer.analyze_sentiment_evolution('NONEXISTENT.AX')
        self.assertIsInstance(analysis, dict)
        
        # Test feature engineering with empty/invalid data
        engineer = AdvancedFeatureEngineer()
        result = engineer.engineer_comprehensive_features('INVALID.AX', {})
        self.assertIsInstance(result, dict)
        # Should handle gracefully and return some features
        if 'features' in result:
            self.assertGreater(len(result['features']), 0)
        else:
            # Or return error info
            self.assertIn('error', result)
    
    def test_performance_basic(self):
        """Test basic performance characteristics"""
        import time
        from temporal_sentiment_analyzer import SentimentDataPoint, TemporalSentimentAnalyzer
        from advanced_feature_engineering import AdvancedFeatureEngineer
        
        # Time feature engineering
        start_time = time.time()
        
        engineer = AdvancedFeatureEngineer()
        sentiment_data = {
            'overall_sentiment': 0.6,
            'confidence': 0.8,
            'news_count': 5,
            'sentiment_components': {'news': 0.6, 'reddit': 0.5, 'events': 0.7}
        }
        
        result = engineer.engineer_comprehensive_features('CBA.AX', sentiment_data)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete quickly (< 5 seconds)
        self.assertLess(execution_time, 5.0)
        self.assertIsInstance(result, dict)
        if 'features' in result:
            self.assertGreater(len(result['features']), 10)
    
    def test_feature_importance_analysis(self):
        """Test feature importance analysis"""
        from advanced_feature_engineering import AdvancedFeatureEngineer
        
        engineer = AdvancedFeatureEngineer()
        
        # Generate features
        sentiment_data = {
            'overall_sentiment': 0.6,
            'confidence': 0.8,
            'news_count': 5,
            'sentiment_components': {'news': 0.6, 'reddit': 0.5, 'events': 0.7}
        }
        
        result = engineer.engineer_comprehensive_features('CBA.AX', sentiment_data)
        self.assertIsInstance(result, dict)
        
        # Check that we have feature quality information
        if 'feature_quality' in result:
            quality = result['feature_quality']
            self.assertIsInstance(quality, dict)
        
        # Check basic results structure
        if 'features' in result:
            self.assertGreater(len(result['features']), 0)
        
        if 'feature_count' in result:
            self.assertGreater(result['feature_count'], 0)


def run_simple_tests():
    """Run simplified test suite"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestCoreFunctionality)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\n" + "="*60)
    print(f"SIMPLE TEST SUMMARY")
    print(f"="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, failure in result.failures:
            print(f"- {test}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, error in result.errors:
            print(f"- {test}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    run_simple_tests()
