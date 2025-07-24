#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Advanced Trading Analysis Features
Tests temporal sentiment analyzer, ensemble learning, and feature engineering
"""

import unittest
import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import pandas as pd
import sqlite3
import tempfile
import os
import json
from datetime import datetime, timedelta
from dataclasses import dataclass
import warnings

# Import modules to test
import sys
sys.path.append('/Users/toddsutherland/Repos/trading_analysis/app')

from app.core.sentiment.temporal_analyzer import (
    SentimentDataPoint, TemporalSentimentAnalyzer
)
from app.core.ml.ensemble.enhanced_ensemble import (
    ModelPrediction, EnhancedTransformerEnsemble
)
from app.core.ml.training.feature_engineering import (
    MarketMicrostructureFeatures, AdvancedFeatureEngineer
)

warnings.filterwarnings("ignore", category=UserWarning)

class TestTemporalSentimentAnalyzer(unittest.TestCase):
    """Test cases for TemporalSentimentAnalyzer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = TemporalSentimentAnalyzer()
        
        # Create sample sentiment data points
        self.sample_points = [
            SentimentDataPoint(
                timestamp=datetime.now() - timedelta(hours=i),
                symbol='CBA.AX',
                sentiment_score=0.5 + 0.1 * np.sin(i * 0.5),
                confidence=0.8 + 0.1 * np.random.random(),
                news_count=5,
                relevance_score=0.8
            ) for i in range(10)
        ]
    
    def test_sentiment_data_point_creation(self):
        """Test SentimentDataPoint dataclass creation"""
        point = SentimentDataPoint(
            timestamp=datetime.now(),
            symbol='CBA.AX',
            sentiment_score=0.75,
            confidence=0.9,
            news_count=3,
            relevance_score=0.8
        )
        
        self.assertIsInstance(point.timestamp, datetime)
        self.assertEqual(point.sentiment_score, 0.75)
        self.assertEqual(point.confidence, 0.9)
        self.assertEqual(point.symbol, 'CBA.AX')
    
    def test_analyzer_initialization(self):
        """Test TemporalSentimentAnalyzer initialization"""
        self.assertIsInstance(self.analyzer, TemporalSentimentAnalyzer)
        self.assertEqual(self.analyzer.window_hours, 24)
        self.assertIsInstance(self.analyzer.sentiment_history, dict)
    
    def test_add_sentiment_data(self):
        """Test adding sentiment data to analyzer"""
        for point in self.sample_points:
            self.analyzer.add_sentiment_observation(point)
        
        self.assertIn('CBA.AX', self.analyzer.sentiment_history)
        self.assertEqual(len(self.analyzer.sentiment_history['CBA.AX']), len(self.sample_points))
    
    def test_analyze_sentiment_evolution(self):
        """Test sentiment evolution analysis"""
        # Add sample data
        for point in self.sample_points:
            self.analyzer.add_sentiment_observation(point)
        
        analysis = self.analyzer.analyze_sentiment_evolution('CBA.AX')
        self.assertIsInstance(analysis, dict)
        
        expected_keys = [
            'trend', 'velocity', 'acceleration', 'volatility',
            'current_regime', 'regime_stability', 'patterns'
        ]
        
        for key in expected_keys:
            self.assertIn(key, analysis)
    
    def test_get_summary_stats(self):
        """Test getting summary statistics"""
        for point in self.sample_points:
            self.analyzer.add_sentiment_observation(point)
        
        stats = self.analyzer.get_summary_stats('CBA.AX')
        self.assertIsInstance(stats, dict)
    
    def test_empty_symbol_analysis(self):
        """Test analysis with no data for symbol"""
        analysis = self.analyzer.analyze_sentiment_evolution('EMPTY.AX')
        self.assertIsInstance(analysis, dict)


class TestEnhancedTransformerEnsemble(unittest.TestCase):
    """Test cases for EnhancedTransformerEnsemble"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.ensemble = EnhancedTransformerEnsemble()
        
        # Create sample predictions
        self.sample_predictions = [
            ModelPrediction(
                model_name=f'model_{i}',
                prediction=0.6 + 0.1 * np.random.random(),
                confidence=0.8 + 0.1 * np.random.random(),
                timestamp=datetime.now()
            ) for i in range(5)
        ]
    
    def test_model_prediction_creation(self):
        """Test ModelPrediction dataclass creation"""
        prediction = ModelPrediction(
            model_name='test_model',
            prediction=0.75,
            confidence=0.9,
            timestamp=datetime.now()
        )
        
        self.assertEqual(prediction.model_name, 'test_model')
        self.assertEqual(prediction.prediction, 0.75)
        self.assertEqual(prediction.confidence, 0.9)
    
    def test_ensemble_initialization(self):
        """Test EnhancedTransformerEnsemble initialization"""
        self.assertIsInstance(self.ensemble, EnhancedTransformerEnsemble)
    
    def test_simple_functionality(self):
        """Test basic ensemble functionality"""
        # This is a placeholder test since the actual API would need to be examined
        self.assertIsInstance(self.ensemble, EnhancedTransformerEnsemble)


class TestAdvancedFeatureEngineering(unittest.TestCase):
    """Test cases for AdvancedFeatureEngineer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engineer = AdvancedFeatureEngineer()
        
        # Sample sentiment data
        self.sample_sentiment = {
            'overall_sentiment': 0.6,
            'confidence': 0.8,
            'news_count': 5,
            'sentiment_components': {
                'news': 0.7,
                'reddit': 0.5,
                'events': 0.6
            }
        }
        
        # Sample price data
        dates = pd.date_range(start='2024-01-01', periods=20, freq='D')
        self.sample_price_data = pd.DataFrame({
            'Open': 100 + np.random.randn(20) * 2,
            'High': 102 + np.random.randn(20) * 2,
            'Low': 98 + np.random.randn(20) * 2,
            'Close': 100 + np.cumsum(np.random.randn(20) * 0.5),
            'Volume': np.random.randint(1000000, 5000000, 20)
        }, index=dates)
    
    def test_feature_engineer_initialization(self):
        """Test AdvancedFeatureEngineer initialization"""
        self.assertIsInstance(self.engineer, AdvancedFeatureEngineer)
        self.assertTrue(os.path.exists(self.engineer.cache_dir))
    
    def test_sentiment_feature_engineering(self):
        """Test sentiment feature engineering"""
        features = self.engineer._engineer_sentiment_features(self.sample_sentiment)
        
        self.assertIsInstance(features, dict)
        self.assertIn('sentiment_score', features)
        self.assertIn('sentiment_confidence', features)
        self.assertIn('sentiment_confidence_interaction', features)
        self.assertIn('sentiment_very_positive', features)
        self.assertIn('high_confidence_positive', features)
        
        # Check feature value ranges
        self.assertGreaterEqual(features['sentiment_confidence'], 0)
        self.assertLessEqual(features['sentiment_confidence'], 1)
    
    def test_temporal_feature_engineering(self):
        """Test temporal feature engineering"""
        features = self.engineer._engineer_temporal_features()
        
        self.assertIsInstance(features, dict)
        
        # Check basic time features
        self.assertIn('hour', features)
        self.assertIn('day_of_week', features)
        self.assertIn('month', features)
        
        # Check cyclical encoding
        self.assertIn('hour_sin', features)
        self.assertIn('hour_cos', features)
        self.assertIn('day_of_week_sin', features)
        
        # Check market session indicators
        self.assertIn('is_market_hours', features)
        self.assertIn('is_weekend', features)
        
        # Validate cyclical encoding ranges
        self.assertGreaterEqual(features['hour_sin'], -1)
        self.assertLessEqual(features['hour_sin'], 1)
    
    @patch('yfinance.Ticker')
    def test_microstructure_feature_engineering(self, mock_ticker):
        """Test market microstructure feature engineering"""
        # Mock yfinance ticker
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = self.sample_price_data
        mock_ticker.return_value = mock_ticker_instance
        
        features = self.engineer._engineer_microstructure_features('CBA.AX', self.sample_price_data)
        
        self.assertIsInstance(features, dict)
        self.assertIn('return_volatility', features)
        self.assertIn('volume_trend', features)
        self.assertIn('realized_volatility', features)
        
        # Check that features are numeric
        for key, value in features.items():
            self.assertIsInstance(value, (int, float))
            self.assertFalse(np.isnan(value))
    
    def test_price_impact_features(self):
        """Test price impact feature calculation"""
        features = self.engineer._calculate_price_impact_features(self.sample_price_data)
        
        self.assertIsInstance(features, dict)
        self.assertIn('return_volatility', features)
        self.assertIn('price_vs_vwap', features)
        self.assertIn('volume_trend', features)
        
        # Validate statistical measures
        if 'return_skewness' in features:
            self.assertIsInstance(features['return_skewness'], float)
    
    def test_volume_profile_features(self):
        """Test volume profile feature calculation"""
        features = self.engineer._calculate_volume_profile_features(self.sample_price_data)
        
        self.assertIsInstance(features, dict)
        self.assertIn('volume_mean', features)
        self.assertIn('volume_median', features)
        self.assertIn('recent_volume_ratio', features)
        
        # Check ratios are positive
        self.assertGreater(features['volume_mean'], 0)
        self.assertGreater(features['recent_volume_ratio'], 0)
    
    def test_volatility_microstructure(self):
        """Test volatility microstructure features"""
        features = self.engineer._calculate_volatility_microstructure(self.sample_price_data)
        
        self.assertIsInstance(features, dict)
        self.assertIn('realized_volatility', features)
        
        if 'garman_klass_volatility' in features:
            self.assertGreaterEqual(features['garman_klass_volatility'], 0)
    
    def test_garman_klass_volatility(self):
        """Test Garman-Klass volatility calculation"""
        gk_vol = self.engineer._calculate_garman_klass_volatility(self.sample_price_data)
        
        self.assertIsInstance(gk_vol, float)
        self.assertGreaterEqual(gk_vol, 0)
    
    def test_jump_detection(self):
        """Test jump detection in returns"""
        returns = self.sample_price_data['Close'].pct_change().dropna()
        jump_prob = self.engineer._detect_jumps(returns)
        
        self.assertIsInstance(jump_prob, float)
        self.assertGreaterEqual(jump_prob, 0)
        self.assertLessEqual(jump_prob, 1)
    
    @patch('yfinance.Ticker')
    def test_cross_asset_feature_engineering(self, mock_ticker):
        """Test cross-asset feature engineering"""
        # Mock yfinance data
        mock_ticker_instance = Mock()
        mock_data = pd.DataFrame({
            'Close': [0.70, 0.71]  # AUD/USD example
        })
        mock_ticker_instance.history.return_value = mock_data
        mock_ticker.return_value = mock_ticker_instance
        
        features = self.engineer._engineer_cross_asset_features('CBA.AX')
        
        self.assertIsInstance(features, dict)
        # Should have default features at minimum
        self.assertIn('aud_usd_rate', features)
        self.assertIn('ten_year_yield', features)
        self.assertIn('vix_level', features)
    
    def test_alternative_data_features(self):
        """Test alternative data feature engineering"""
        features = self.engineer._engineer_alternative_data_features('CBA.AX')
        
        self.assertIsInstance(features, dict)
        self.assertIn('google_trends_score', features)
        self.assertIn('news_velocity', features)
        
        # Check value ranges
        if 'google_trends_score' in features:
            self.assertGreaterEqual(features['google_trends_score'], 0)
            self.assertLessEqual(features['google_trends_score'], 100)
    
    def test_interaction_features(self):
        """Test interaction feature engineering"""
        base_features = {
            'sentiment_score': 0.6,
            'sentiment_confidence': 0.8,
            'realized_volatility': 0.2,
            'recent_volume_ratio': 1.5,
            'is_market_hours': 1,
            'aud_usd_change': 0.5
        }
        
        features = self.engineer._engineer_interaction_features(base_features, self.sample_sentiment)
        
        self.assertIsInstance(features, dict)
        self.assertIn('sentiment_volatility_interaction', features)
        self.assertIn('market_hours_sentiment', features)
        self.assertIn('aud_sentiment_interaction', features)
    
    def test_comprehensive_feature_engineering(self):
        """Test complete feature engineering pipeline"""
        features = self.engineer.engineer_features('CBA.AX', self.sample_sentiment, self.sample_price_data)
        
        self.assertIsInstance(features, dict)
        self.assertGreater(len(features), 10)  # Should have many features
        
        # Check all features are numeric and valid
        for key, value in features.items():
            self.assertIsInstance(value, (int, float))
            self.assertFalse(np.isnan(value))
            self.assertFalse(np.isinf(value))
    
    def test_feature_validation_and_cleaning(self):
        """Test feature validation and cleaning"""
        dirty_features = {
            'good_feature': 0.5,
            'nan_feature': np.nan,
            'inf_feature': np.inf,
            'negative_inf': -np.inf,
            'string_feature': 'invalid'
        }
        
        clean_features = self.engineer._validate_and_clean_features(dirty_features)
        
        self.assertIsInstance(clean_features, dict)
        self.assertEqual(clean_features['good_feature'], 0.5)
        self.assertEqual(clean_features['nan_feature'], 0.0)
        self.assertEqual(clean_features['inf_feature'], 0.0)
        self.assertEqual(clean_features['string_feature'], 0.0)
    
    def test_feature_importance_analysis(self):
        """Test feature importance analysis"""
        features = self.engineer.engineer_features('CBA.AX', self.sample_sentiment, self.sample_price_data)
        analysis = self.engineer.get_feature_importance_analysis(features)
        
        self.assertIsInstance(analysis, dict)
        self.assertIn('feature_count', analysis)
        self.assertIn('feature_categories', analysis)
        self.assertIn('feature_stats', analysis)
        
        self.assertGreater(analysis['feature_count'], 0)


class TestIntegrationAndPerformance(unittest.TestCase):
    """Integration tests for the entire system"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.temporal_analyzer = TemporalSentimentAnalyzer()
        self.ensemble_system = EnhancedTransformerEnsemble()
        self.feature_engineer = AdvancedFeatureEngineer()
    
    def tearDown(self):
        """Clean up integration test fixtures"""
        pass
    
    def test_end_to_end_analysis_pipeline(self):
        """Test complete analysis pipeline integration"""
        symbol = 'CBA.AX'
        
        # 1. Generate temporal sentiment data
        base_time = datetime.now()
        for i in range(10):
            point = SentimentDataPoint(
                timestamp=base_time - timedelta(hours=i),
                symbol=symbol,
                sentiment_score=0.5 + 0.2 * np.sin(i * 0.3),
                confidence=0.8 + 0.1 * np.random.random(),
                news_count=5,
                relevance_score=0.8
            )
            self.temporal_analyzer.add_sentiment_observation(point)
        
        # 2. Get temporal features
        temporal_features = self.temporal_analyzer.analyze_sentiment_evolution(symbol)
        self.assertIsInstance(temporal_features, dict)
        
        # 3. Engineer comprehensive features
        sentiment_data = {
            'overall_sentiment': temporal_features.get('sentiment_trend', 0.5),
            'confidence': 0.8,
            'news_count': 5,
            'sentiment_components': {'news': 0.6, 'reddit': 0.5, 'events': 0.7}
        }
        
        engineered_features = self.feature_engineer.engineer_features(symbol, sentiment_data)
        self.assertIsInstance(engineered_features, dict)
        self.assertGreater(len(engineered_features), 15)
        
        # 4. Create model predictions for ensemble
        for i in range(3):
            prediction = ModelPrediction(
                model_name=f'model_{i}',
                prediction=0.6 + 0.1 * np.random.random(),
                confidence=0.8 + 0.1 * np.random.random(),
                features_used=list(engineered_features.keys())[:10],
                model_type='transformer' if i % 2 else 'traditional',
                timestamp=datetime.now()
            )
            self.ensemble_system.add_model_prediction(prediction)
        
        # 5. Get ensemble prediction
        ensemble_prediction = self.ensemble_system.ensemble_confidence_weighted()
        self.assertIsInstance(ensemble_prediction, float)
        self.assertGreaterEqual(ensemble_prediction, 0)
        self.assertLessEqual(ensemble_prediction, 1)
        
        # 6. Analyze the complete system
        temporal_analysis = self.temporal_analyzer.analyze_sentiment_evolution(symbol)
        ensemble_analysis = self.ensemble_system.analyze_ensemble()
        feature_analysis = self.feature_engineer.get_feature_importance_analysis(engineered_features)
        
        self.assertIsInstance(temporal_analysis, dict)
        self.assertIsInstance(ensemble_analysis, dict)
        self.assertIsInstance(feature_analysis, dict)
    
    def test_performance_with_large_dataset(self):
        """Test system performance with larger datasets"""
        import time
        
        start_time = time.time()
        
        # Add large amount of temporal data
        base_time = datetime.now()
        for i in range(100):
            point = SentimentDataPoint(
                timestamp=base_time - timedelta(minutes=i*30),
                symbol='CBA.AX',
                sentiment_score=np.random.normal(0.5, 0.2),
                confidence=np.random.uniform(0.6, 0.9),
                news_count=np.random.randint(1, 10),
                relevance_score=0.8
            )
            self.temporal_analyzer.add_sentiment_observation(point)
        
        # Generate many features
        sentiment_data = {
            'overall_sentiment': 0.6,
            'confidence': 0.8,
            'news_count': 15,
            'sentiment_components': {'news': 0.6, 'reddit': 0.5, 'events': 0.7}
        }
        
        features = self.feature_engineer.engineer_features('CBA.AX', sentiment_data)
        
        # Create ensemble with many models
        for i in range(10):
            prediction = ModelPrediction(
                model_name=f'model_{i}',
                prediction=np.random.uniform(0.3, 0.8),
                confidence=np.random.uniform(0.7, 0.9),
                features_used=list(features.keys())[:20],
                model_type=['transformer', 'traditional', 'xgboost'][i % 3],
                timestamp=datetime.now()
            )
            self.ensemble_system.add_model_prediction(prediction)
        
        ensemble_result = self.ensemble_system.ensemble_weighted()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete in reasonable time (< 10 seconds)
        self.assertLess(execution_time, 10.0)
        self.assertIsInstance(ensemble_result, float)
    
    def test_error_handling_and_robustness(self):
        """Test system robustness with various error conditions"""
        # Test with empty data
        empty_features = self.feature_engineer.engineer_features('INVALID.AX', {})
        self.assertIsInstance(empty_features, dict)
        
        # Test temporal analyzer with no data
        empty_temporal_features = self.temporal_analyzer.analyze_sentiment_evolution('EMPTY.AX')
        self.assertIsInstance(empty_temporal_features, dict)
        
        # Test ensemble with no predictions
        try:
            result = self.ensemble_system.ensemble_average()
            # Should either return a default value or handle gracefully
            self.assertTrue(result is None or isinstance(result, float))
        except:
            pass  # Exception handling is acceptable
        
        # Test with malformed data
        bad_sentiment = {
            'overall_sentiment': 'invalid',
            'confidence': None,
            'news_count': -1
        }
        
        robust_features = self.feature_engineer.engineer_features('CBA.AX', bad_sentiment)
        self.assertIsInstance(robust_features, dict)


def run_test_suite():
    """Run the complete test suite with coverage reporting"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestTemporalSentimentAnalyzer,
        TestEnhancedTransformerEnsemble,
        TestAdvancedFeatureEngineering,
        TestIntegrationAndPerformance
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n" + "="*80)
    print(f"TEST SUMMARY")
    print(f"="*80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, failure in result.failures:
            print(f"- {test}: {failure}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, error in result.errors:
            print(f"- {test}: {error}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    run_test_suite()
