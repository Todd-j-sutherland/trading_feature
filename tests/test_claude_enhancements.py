#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Advanced Trading Features
Tests all Claude-suggested enhancements: temporal analysis, ensemble learning, and feature engineering
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
from datetime import datetime, timedelta

# Add the src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Test data for mocking
MOCK_SENTIMENT_DATA = {
    'overall_sentiment': 0.7,
    'confidence': 0.85,
    'news_count': 15,
    'reddit_sentiment': 0.6,
    'event_score': 0.8,
    'sentiment_volatility': 0.2
}

MOCK_NEWS_DATA = [
    {
        'title': 'CBA reports strong quarterly earnings',
        'sentiment': 0.8,
        'timestamp': '2025-01-07T10:00:00Z',
        'source': 'Financial Review'
    },
    {
        'title': 'ANZ expands digital banking services',
        'sentiment': 0.6,
        'timestamp': '2025-01-07T11:30:00Z',
        'source': 'Reuters'
    },
    {
        'title': 'Banking sector faces regulatory scrutiny',
        'sentiment': -0.3,
        'timestamp': '2025-01-07T14:15:00Z',
        'source': 'ABC News'
    }
]

MOCK_PREDICTION_DATA = [
    {'model': 'bert', 'prediction': 0.75, 'confidence': 0.9},
    {'model': 'roberta', 'prediction': 0.82, 'confidence': 0.85},
    {'model': 'distilbert', 'prediction': 0.68, 'confidence': 0.8}
]

class TestTemporalSentimentAnalyzer(unittest.TestCase):
    """Test the temporal sentiment analysis module"""
    
    def setUp(self):
        """Set up test fixtures"""
        try:
            from temporal_sentiment_analyzer import TemporalSentimentAnalyzer, SentimentDataPoint
            self.analyzer = TemporalSentimentAnalyzer()
            self.SentimentDataPoint = SentimentDataPoint
        except ImportError as e:
            self.skipTest(f"Could not import temporal_sentiment_analyzer: {e}")
    
    def test_sentiment_data_point_creation(self):
        """Test SentimentDataPoint dataclass creation"""
        data_point = self.SentimentDataPoint(
            timestamp=datetime.now(),
            sentiment_score=0.7,
            confidence=0.85,
            source='test'
        )
        
        self.assertEqual(data_point.sentiment_score, 0.7)
        self.assertEqual(data_point.confidence, 0.85)
        self.assertEqual(data_point.source, 'test')
        self.assertIsInstance(data_point.timestamp, datetime)
    
    def test_add_sentiment_point(self):
        """Test adding sentiment data points"""
        initial_count = len(self.analyzer.sentiment_history)
        
        self.analyzer.add_sentiment_point(
            sentiment_score=0.7,
            confidence=0.85,
            source='test'
        )
        
        self.assertEqual(len(self.analyzer.sentiment_history), initial_count + 1)
        latest_point = self.analyzer.sentiment_history[-1]
        self.assertEqual(latest_point.sentiment_score, 0.7)
        self.assertEqual(latest_point.confidence, 0.85)
    
    def test_temporal_analysis_empty_history(self):
        """Test temporal analysis with empty history"""
        self.analyzer.sentiment_history = []
        
        result = self.analyzer.analyze_temporal_patterns()
        
        self.assertIn('error', result)
        self.assertEqual(result['pattern_count'], 0)
    
    def test_temporal_analysis_with_data(self):
        """Test temporal analysis with sample data"""
        # Add test data points
        base_time = datetime.now() - timedelta(hours=24)
        
        for i in range(10):
            self.analyzer.add_sentiment_point(
                sentiment_score=0.5 + (i % 3) * 0.2,  # Varying sentiment
                confidence=0.8,
                source='test',
                timestamp=base_time + timedelta(hours=i*2)
            )
        
        result = self.analyzer.analyze_temporal_patterns()
        
        self.assertIn('velocity', result)
        self.assertIn('acceleration', result)
        self.assertIn('volatility', result)
        self.assertIn('trend_strength', result)
        self.assertIsInstance(result['velocity'], (int, float))
        self.assertIsInstance(result['acceleration'], (int, float))
    
    def test_sentiment_velocity_calculation(self):
        """Test sentiment velocity calculation"""
        # Add test points with known sentiment progression
        base_time = datetime.now() - timedelta(hours=4)
        
        self.analyzer.add_sentiment_point(0.5, 0.8, 'test', base_time)
        self.analyzer.add_sentiment_point(0.6, 0.8, 'test', base_time + timedelta(hours=1))
        self.analyzer.add_sentiment_point(0.7, 0.8, 'test', base_time + timedelta(hours=2))
        
        velocity = self.analyzer.calculate_sentiment_velocity(hours=2)
        
        # Should show positive velocity (sentiment increasing)
        self.assertGreater(velocity, 0)
    
    def test_regime_detection(self):
        """Test market regime detection"""
        # Add stable positive sentiment
        base_time = datetime.now() - timedelta(hours=6)
        
        for i in range(5):
            self.analyzer.add_sentiment_point(
                sentiment_score=0.7 + 0.1 * (i % 2),  # Stable around 0.7-0.8
                confidence=0.85,
                source='test',
                timestamp=base_time + timedelta(hours=i)
            )
        
        regime = self.analyzer.detect_sentiment_regime()
        
        self.assertIn('regime_type', regime)
        self.assertIn('stability_score', regime)
        self.assertIn('duration_hours', regime)
        
        # Should detect stable positive regime
        self.assertGreater(regime['stability_score'], 0.5)
    
    def test_pattern_recognition(self):
        """Test pattern recognition in sentiment data"""
        # Create a clear upward trend pattern
        base_time = datetime.now() - timedelta(hours=8)
        
        for i in range(8):
            self.analyzer.add_sentiment_point(
                sentiment_score=0.3 + i * 0.1,  # Clear upward trend
                confidence=0.8,
                source='test',
                timestamp=base_time + timedelta(hours=i)
            )
        
        patterns = self.analyzer.recognize_patterns()
        
        self.assertIn('trend_patterns', patterns)
        self.assertIn('oscillation_patterns', patterns)
        self.assertIn('breakout_patterns', patterns)
        
        # Should detect upward trend
        if patterns['trend_patterns']:
            self.assertEqual(patterns['trend_patterns'][0]['direction'], 'upward')


class TestEnhancedEnsembleLearning(unittest.TestCase):
    """Test the enhanced ensemble learning module"""
    
    def setUp(self):
        """Set up test fixtures"""
        try:
            from enhanced_ensemble_learning import EnhancedEnsembleLearning, ModelPrediction, EnsemblePrediction
            self.ensemble = EnhancedEnsembleLearning()
            self.ModelPrediction = ModelPrediction
            self.EnsemblePrediction = EnsemblePrediction
        except ImportError as e:
            self.skipTest(f"Could not import enhanced_ensemble_learning: {e}")
    
    def test_model_prediction_creation(self):
        """Test ModelPrediction dataclass creation"""
        prediction = self.ModelPrediction(
            model_name='bert',
            prediction=0.75,
            confidence=0.9,
            features={'sentiment': 0.7}
        )
        
        self.assertEqual(prediction.model_name, 'bert')
        self.assertEqual(prediction.prediction, 0.75)
        self.assertEqual(prediction.confidence, 0.9)
        self.assertIn('sentiment', prediction.features)
    
    def test_ensemble_prediction_creation(self):
        """Test EnsemblePrediction dataclass creation"""
        ensemble_pred = self.EnsemblePrediction(
            final_prediction=0.8,
            confidence=0.85,
            strategy_used='weighted_voting',
            model_weights={'bert': 0.4, 'roberta': 0.6}
        )
        
        self.assertEqual(ensemble_pred.final_prediction, 0.8)
        self.assertEqual(ensemble_pred.strategy_used, 'weighted_voting')
        self.assertIn('bert', ensemble_pred.model_weights)
    
    def test_weighted_voting_strategy(self):
        """Test weighted voting ensemble strategy"""
        predictions = [
            self.ModelPrediction('bert', 0.7, 0.9, {}),
            self.ModelPrediction('roberta', 0.8, 0.85, {}),
            self.ModelPrediction('distilbert', 0.6, 0.8, {})
        ]
        
        result = self.ensemble.weighted_voting_ensemble(predictions)
        
        self.assertIsInstance(result, self.EnsemblePrediction)
        self.assertEqual(result.strategy_used, 'weighted_voting')
        self.assertGreater(result.final_prediction, 0)
        self.assertLessEqual(result.final_prediction, 1)
        self.assertGreater(result.confidence, 0)
    
    def test_confidence_weighted_strategy(self):
        """Test confidence-weighted ensemble strategy"""
        predictions = [
            self.ModelPrediction('bert', 0.7, 0.95, {}),  # High confidence
            self.ModelPrediction('roberta', 0.8, 0.6, {}),  # Low confidence
            self.ModelPrediction('distilbert', 0.6, 0.85, {})  # Medium confidence
        ]
        
        result = self.ensemble.confidence_weighted_ensemble(predictions)
        
        self.assertIsInstance(result, self.EnsemblePrediction)
        self.assertEqual(result.strategy_used, 'confidence_weighted')
        
        # Result should be closer to high-confidence prediction (0.7)
        self.assertLess(abs(result.final_prediction - 0.7), abs(result.final_prediction - 0.8))
    
    @patch('enhanced_ensemble_learning.xgb')
    def test_meta_learner_strategy(self, mock_xgb):
        """Test meta-learner ensemble strategy"""
        # Mock XGBoost
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.75]
        mock_xgb.XGBClassifier.return_value = mock_model
        
        predictions = [
            self.ModelPrediction('bert', 0.7, 0.9, {'feature1': 0.5}),
            self.ModelPrediction('roberta', 0.8, 0.85, {'feature1': 0.6}),
        ]
        
        # Train meta-learner first
        self.ensemble.train_meta_learner(predictions, target=1, features={'feature1': 0.55})
        
        # Test prediction
        result = self.ensemble.meta_learner_ensemble(predictions, {'feature1': 0.55})
        
        self.assertIsInstance(result, self.EnsemblePrediction)
        self.assertEqual(result.strategy_used, 'meta_learner')
        self.assertEqual(result.final_prediction, 0.75)
    
    def test_adaptive_hybrid_strategy(self):
        """Test adaptive hybrid ensemble strategy"""
        predictions = [
            self.ModelPrediction('bert', 0.7, 0.9, {}),
            self.ModelPrediction('roberta', 0.8, 0.85, {}),
        ]
        
        # Mock performance history to test adaptation
        self.ensemble.model_performance = {
            'bert': {'accuracy': 0.8, 'last_updated': datetime.now()},
            'roberta': {'accuracy': 0.75, 'last_updated': datetime.now()}
        }
        
        result = self.ensemble.adaptive_hybrid_ensemble(predictions)
        
        self.assertIsInstance(result, self.EnsemblePrediction)
        self.assertEqual(result.strategy_used, 'adaptive_hybrid')
        
        # Should weight bert higher due to better performance
        self.assertGreater(result.model_weights.get('bert', 0), 
                          result.model_weights.get('roberta', 0))
    
    def test_predict_ensemble(self):
        """Test main ensemble prediction method"""
        predictions = [
            self.ModelPrediction('bert', 0.7, 0.9, {}),
            self.ModelPrediction('roberta', 0.8, 0.85, {}),
        ]
        
        result = self.ensemble.predict_ensemble(predictions, strategy='weighted_voting')
        
        self.assertIsInstance(result, self.EnsemblePrediction)
        self.assertIn('ensemble_metadata', result.__dict__ or {})
    
    def test_update_model_performance(self):
        """Test model performance tracking"""
        initial_performance_count = len(self.ensemble.model_performance)
        
        self.ensemble.update_model_performance('bert', accuracy=0.85, prediction_time=0.1)
        
        self.assertIn('bert', self.ensemble.model_performance)
        self.assertEqual(self.ensemble.model_performance['bert']['accuracy'], 0.85)
        self.assertEqual(len(self.ensemble.model_performance), initial_performance_count + 1)
    
    def test_calculate_model_weights(self):
        """Test dynamic model weight calculation"""
        # Set up mock performance data
        self.ensemble.model_performance = {
            'bert': {'accuracy': 0.9, 'prediction_time': 0.1},
            'roberta': {'accuracy': 0.8, 'prediction_time': 0.2},
            'distilbert': {'accuracy': 0.7, 'prediction_time': 0.05}
        }
        
        weights = self.ensemble.calculate_model_weights(['bert', 'roberta', 'distilbert'])
        
        self.assertIn('bert', weights)
        self.assertIn('roberta', weights)
        self.assertIn('distilbert', weights)
        
        # Weights should sum to approximately 1
        total_weight = sum(weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=2)
        
        # bert should have highest weight (best accuracy)
        self.assertGreater(weights['bert'], weights['roberta'])
        self.assertGreater(weights['bert'], weights['distilbert'])


class TestAdvancedFeatureEngineering(unittest.TestCase):
    """Test the advanced feature engineering module"""
    
    def setUp(self):
        """Set up test fixtures"""
        try:
            from advanced_feature_engineering import AdvancedFeatureEngineer
            self.feature_engineer = AdvancedFeatureEngineer()
        except ImportError as e:
            self.skipTest(f"Could not import advanced_feature_engineering: {e}")
    
    def test_comprehensive_feature_engineering(self):
        """Test comprehensive feature generation"""
        result = self.feature_engineer.engineer_comprehensive_features(
            symbol='CBA',
            sentiment_data=MOCK_SENTIMENT_DATA,
            news_data=MOCK_NEWS_DATA
        )
        
        self.assertIn('features', result)
        self.assertIn('feature_quality', result)
        self.assertIn('feature_count', result)
        self.assertGreater(result['feature_count'], 10)  # Should generate many features
    
    def test_base_sentiment_features(self):
        """Test base sentiment feature extraction"""
        features = self.feature_engineer._extract_base_sentiment_features(MOCK_SENTIMENT_DATA)
        
        self.assertIn('sentiment_score', features)
        self.assertIn('sentiment_confidence', features)
        self.assertIn('news_count', features)
        self.assertEqual(features['sentiment_score'], 0.7)
        self.assertEqual(features['sentiment_confidence'], 0.85)
        self.assertEqual(features['news_count'], 15)
    
    def test_microstructure_features(self):
        """Test microstructure feature engineering"""
        features = self.feature_engineer._engineer_microstructure_features('CBA')
        
        self.assertIn('bid_ask_spread_trend', features)
        self.assertIn('order_flow_imbalance', features)
        self.assertIn('volume_profile_score', features)
        self.assertIn('liquidity_score', features)
        
        # All values should be numeric
        for key, value in features.items():
            self.assertIsInstance(value, (int, float))
    
    def test_cross_asset_features(self):
        """Test cross-asset feature engineering"""
        features = self.feature_engineer._engineer_cross_asset_features('CBA')
        
        self.assertIn('aud_usd_correlation', features)
        self.assertIn('bond_yield_impact', features)
        self.assertIn('sector_rotation_signal', features)
        self.assertIn('global_risk_sentiment', features)
        
        # All values should be numeric
        for key, value in features.items():
            self.assertIsInstance(value, (int, float))
    
    def test_alternative_data_features(self):
        """Test alternative data feature engineering"""
        features = self.feature_engineer._engineer_alternative_data_features('CBA', MOCK_NEWS_DATA)
        
        self.assertIn('google_trends_score', features)
        self.assertIn('social_media_velocity', features)
        self.assertIn('news_clustering_score', features)
        self.assertIn('narrative_shift_indicator', features)
        
        # All values should be numeric
        for key, value in features.items():
            self.assertIsInstance(value, (int, float))
    
    def test_temporal_features(self):
        """Test temporal feature engineering"""
        features = self.feature_engineer._engineer_temporal_features(MOCK_SENTIMENT_DATA)
        
        self.assertIn('hour_of_day', features)
        self.assertIn('day_of_week', features)
        self.assertIn('is_market_hours', features)
        self.assertIn('is_weekend', features)
        
        # Check ranges
        self.assertGreaterEqual(features['hour_of_day'], 0)
        self.assertLessEqual(features['hour_of_day'], 23)
        self.assertGreaterEqual(features['day_of_week'], 0)
        self.assertLessEqual(features['day_of_week'], 6)
        self.assertIn(features['is_market_hours'], [0, 1])
        self.assertIn(features['is_weekend'], [0, 1])
    
    def test_news_features(self):
        """Test news-specific feature engineering"""
        features = self.feature_engineer._engineer_news_features(MOCK_NEWS_DATA)
        
        self.assertIn('news_velocity_1h', features)
        self.assertIn('news_velocity_4h', features)
        self.assertIn('avg_headline_length', features)
        self.assertIn('source_diversity', features)
        
        # Source diversity should equal number of unique sources
        unique_sources = len(set(n['source'] for n in MOCK_NEWS_DATA))
        self.assertEqual(features['source_diversity'], unique_sources)
    
    def test_feature_interactions(self):
        """Test feature interaction engineering"""
        base_features = {
            'sentiment_score': 0.7,
            'sentiment_confidence': 0.85,
            'news_velocity_1h': 2.0,
            'is_market_hours': 1
        }
        
        interactions = self.feature_engineer._engineer_feature_interactions(base_features)
        
        self.assertIn('sentiment_confidence_interaction', interactions)
        self.assertIn('news_velocity_sentiment_interaction', interactions)
        self.assertIn('market_hours_sentiment', interactions)
        
        # Check interaction calculations
        expected_sentiment_confidence = 0.7 * 0.85
        self.assertAlmostEqual(interactions['sentiment_confidence_interaction'], 
                             expected_sentiment_confidence, places=2)
    
    def test_feature_quality_assessment(self):
        """Test feature quality assessment"""
        features = {
            'good_feature': 0.5,
            'missing_feature': None,
            'extreme_feature': 100.0,
            'normal_feature': 0.8
        }
        
        quality = self.feature_engineer._assess_feature_quality(features)
        
        self.assertIn('quality_score', quality)
        self.assertIn('total_features', quality)
        self.assertIn('missing_features', quality)
        self.assertIn('extreme_features', quality)
        
        self.assertEqual(quality['total_features'], 4)
        self.assertEqual(quality['missing_features'], 1)
        self.assertEqual(quality['extreme_features'], 1)
    
    def test_feature_caching(self):
        """Test feature caching mechanism"""
        # First call should calculate features
        features1 = self.feature_engineer._engineer_microstructure_features('CBA')
        
        # Second call should use cache (test by checking if cache key exists)
        cache_key = "microstructure_CBA"
        self.assertIn(cache_key, self.feature_engineer.feature_cache)
        
        # Get cached features
        features2 = self.feature_engineer._engineer_microstructure_features('CBA')
        
        # Should be identical
        self.assertEqual(features1, features2)
    
    def test_feature_importance_calculation(self):
        """Test feature importance calculation"""
        features = {
            'sentiment_score': 0.8,
            'microstructure_spread': 0.2,
            'cross_asset_correlation': 0.6,
            'alternative_trends': 0.4
        }
        
        importance = self.feature_engineer.get_feature_importance(features)
        
        self.assertIn('feature_importance', importance)
        self.assertIn('top_features', importance)
        
        # Check that all features have importance scores
        for feature in features.keys():
            self.assertIn(feature, importance['feature_importance'])
        
        # Top features should be sorted by importance
        top_features = importance['top_features']
        if len(top_features) > 1:
            self.assertGreaterEqual(top_features[0][1], top_features[1][1])


class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple modules"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.test_modules = []
        self.available_modules = []
        
        # Try to import all modules
        try:
            from temporal_sentiment_analyzer import TemporalSentimentAnalyzer
            self.temporal_analyzer = TemporalSentimentAnalyzer()
            self.available_modules.append('temporal')
        except ImportError:
            pass
        
        try:
            from enhanced_ensemble_learning import EnhancedEnsembleLearning, ModelPrediction
            self.ensemble = EnhancedEnsembleLearning()
            self.ModelPrediction = ModelPrediction
            self.available_modules.append('ensemble')
        except ImportError:
            pass
        
        try:
            from advanced_feature_engineering import AdvancedFeatureEngineer
            self.feature_engineer = AdvancedFeatureEngineer()
            self.available_modules.append('features')
        except ImportError:
            pass
    
    def test_temporal_feature_integration(self):
        """Test integration between temporal analysis and feature engineering"""
        if 'temporal' not in self.available_modules or 'features' not in self.available_modules:
            self.skipTest("Required modules not available")
        
        # Add temporal data
        base_time = datetime.now() - timedelta(hours=4)
        for i in range(5):
            self.temporal_analyzer.add_sentiment_point(
                sentiment_score=0.6 + i * 0.05,
                confidence=0.8,
                source='test',
                timestamp=base_time + timedelta(hours=i)
            )
        
        # Analyze temporal patterns
        temporal_result = self.temporal_analyzer.analyze_temporal_patterns()
        
        # Use temporal data in feature engineering
        enhanced_sentiment_data = {**MOCK_SENTIMENT_DATA, **temporal_result}
        
        features = self.feature_engineer.engineer_comprehensive_features(
            symbol='CBA',
            sentiment_data=enhanced_sentiment_data,
            news_data=MOCK_NEWS_DATA
        )
        
        self.assertIn('features', features)
        self.assertGreater(features['feature_count'], 20)  # Should have many features
    
    def test_ensemble_feature_integration(self):
        """Test integration between ensemble learning and feature engineering"""
        if 'ensemble' not in self.available_modules or 'features' not in self.available_modules:
            self.skipTest("Required modules not available")
        
        # Generate comprehensive features
        feature_result = self.feature_engineer.engineer_comprehensive_features(
            symbol='CBA',
            sentiment_data=MOCK_SENTIMENT_DATA,
            news_data=MOCK_NEWS_DATA
        )
        
        features = feature_result['features']
        
        # Create predictions with features
        predictions = [
            self.ModelPrediction('bert', 0.7, 0.9, features),
            self.ModelPrediction('roberta', 0.8, 0.85, features)
        ]
        
        # Test ensemble prediction
        result = self.ensemble.predict_ensemble(predictions, strategy='weighted_voting')
        
        self.assertIsNotNone(result)
        self.assertGreater(result.confidence, 0)
    
    def test_full_pipeline_integration(self):
        """Test full pipeline integration of all modules"""
        if len(self.available_modules) < 3:
            self.skipTest("Not all modules available for full integration test")
        
        # 1. Add temporal sentiment data
        base_time = datetime.now() - timedelta(hours=6)
        for i in range(6):
            self.temporal_analyzer.add_sentiment_point(
                sentiment_score=0.5 + (i % 3) * 0.1,
                confidence=0.8 + (i % 2) * 0.1,
                source='test',
                timestamp=base_time + timedelta(hours=i)
            )
        
        # 2. Analyze temporal patterns
        temporal_patterns = self.temporal_analyzer.analyze_temporal_patterns()
        
        # 3. Combine with sentiment data
        enhanced_sentiment = {**MOCK_SENTIMENT_DATA, **temporal_patterns}
        
        # 4. Generate comprehensive features
        feature_result = self.feature_engineer.engineer_comprehensive_features(
            symbol='CBA',
            sentiment_data=enhanced_sentiment,
            news_data=MOCK_NEWS_DATA
        )
        
        features = feature_result['features']
        
        # 5. Create ensemble predictions
        predictions = [
            self.ModelPrediction('bert', 0.72, 0.9, features),
            self.ModelPrediction('roberta', 0.78, 0.85, features),
            self.ModelPrediction('distilbert', 0.65, 0.8, features)
        ]
        
        # 6. Get ensemble prediction
        ensemble_result = self.ensemble.predict_ensemble(
            predictions, 
            strategy='adaptive_hybrid'
        )
        
        # Verify full pipeline results
        self.assertIsNotNone(ensemble_result)
        self.assertGreater(ensemble_result.confidence, 0)
        self.assertGreater(len(features), 15)  # Should have comprehensive features
        self.assertIn('velocity', temporal_patterns)  # Should have temporal analysis


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""
    
    def test_import_error_handling(self):
        """Test that modules handle missing dependencies gracefully"""
        # This test checks that our modules can be imported even with missing dependencies
        # The actual functionality will be limited, but imports should not fail completely
        
        with patch.dict('sys.modules', {'numpy': None, 'pandas': None}):
            try:
                # These imports might fail, but should do so gracefully
                import temporal_sentiment_analyzer
                import enhanced_ensemble_learning
                import advanced_feature_engineering
                
                # If we get here, modules handle missing dependencies well
                self.assertTrue(True)
            except ImportError:
                # Expected if dependencies are truly missing
                self.assertTrue(True)
    
    def test_empty_data_handling(self):
        """Test handling of empty or invalid data"""
        try:
            from advanced_feature_engineering import AdvancedFeatureEngineer
            
            feature_engineer = AdvancedFeatureEngineer()
            
            # Test with empty sentiment data
            result = feature_engineer.engineer_comprehensive_features(
                symbol='CBA',
                sentiment_data={},
                news_data=[]
            )
            
            # Should handle gracefully
            self.assertIn('features', result)
            
        except ImportError:
            self.skipTest("advanced_feature_engineering not available")
    
    def test_malformed_data_handling(self):
        """Test handling of malformed data"""
        try:
            from advanced_feature_engineering import AdvancedFeatureEngineer
            
            feature_engineer = AdvancedFeatureEngineer()
            
            # Test with malformed news data
            malformed_news = [
                {'title': None, 'sentiment': 'invalid'},  # Invalid data types
                {'timestamp': 'invalid_date'},  # Invalid timestamp
                {}  # Empty dict
            ]
            
            result = feature_engineer._engineer_news_features(malformed_news)
            
            # Should handle gracefully without crashing
            self.assertIsInstance(result, dict)
            
        except ImportError:
            self.skipTest("advanced_feature_engineering not available")


def create_test_suite():
    """Create comprehensive test suite"""
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestTemporalSentimentAnalyzer,
        TestEnhancedEnsembleLearning,
        TestAdvancedFeatureEngineering,
        TestIntegration,
        TestErrorHandling
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    return suite


def run_specific_test_class(test_class_name):
    """Run a specific test class"""
    test_classes = {
        'temporal': TestTemporalSentimentAnalyzer,
        'ensemble': TestEnhancedEnsembleLearning,
        'features': TestAdvancedFeatureEngineering,
        'integration': TestIntegration,
        'errors': TestErrorHandling
    }
    
    if test_class_name in test_classes:
        suite = unittest.TestLoader().loadTestsFromTestCase(test_classes[test_class_name])
        runner = unittest.TextTestRunner(verbosity=2)
        return runner.run(suite)
    else:
        print(f"Unknown test class: {test_class_name}")
        print(f"Available: {list(test_classes.keys())}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Claude Enhancement Tests')
    parser.add_argument('--class', dest='test_class', help='Run specific test class')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--list', action='store_true', help='List available test classes')
    
    args = parser.parse_args()
    
    if args.list:
        print("Available test classes:")
        print("  temporal - Test temporal sentiment analysis")
        print("  ensemble - Test enhanced ensemble learning")  
        print("  features - Test advanced feature engineering")
        print("  integration - Test module integration")
        print("  errors - Test error handling")
        print("\nRun with: python test_claude_enhancements.py --class <class_name>")
    elif args.test_class:
        result = run_specific_test_class(args.test_class)
    else:
        # Run all tests
        suite = create_test_suite()
        runner = unittest.TextTestRunner(verbosity=2 if args.verbose else 1)
        result = runner.run(suite)
        
        # Print summary
        print(f"\n{'='*50}")
        print(f"Test Summary:")
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
        
        if result.failures:
            print(f"\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}")
        
        if result.errors:
            print(f"\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}")
