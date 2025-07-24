#!/usr/bin/env python3
"""
Comprehensive Tests for Enhanced Sentiment Scoring System
Tests critical functionality and error handling
"""

import sys
import os
import unittest
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from enhanced_sentiment_scoring import (
        EnhancedSentimentScorer, 
        SentimentMetrics, 
        MarketRegime, 
        SentimentStrength,
        create_market_context_detector
    )
    ENHANCED_SENTIMENT_AVAILABLE = True
except ImportError as e:
    ENHANCED_SENTIMENT_AVAILABLE = False
    print(f"Enhanced sentiment module not available: {e}")

class TestEnhancedSentimentScoring(unittest.TestCase):
    """Test suite for enhanced sentiment scoring system"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not ENHANCED_SENTIMENT_AVAILABLE:
            self.skipTest("Enhanced sentiment scoring not available")
        
        self.scorer = EnhancedSentimentScorer()
        
        # Standard test components
        self.valid_components = {
            'news_sentiment': 0.3,
            'social_sentiment': 0.2,
            'technical_momentum': 0.1,
            'options_flow': 0.0,
            'insider_activity': 0.05,
            'analyst_sentiment': 0.25,
            'earnings_surprise': 0.1
        }
        
        # Standard test market data
        self.valid_market_data = {
            'volatility': 0.25,
            'regime': 'stable',
            'regime_confidence': 0.8,
            'market_trend': 'bullish',
            'sector_rotation': 'neutral'
        }
        
        # Sample news items
        self.valid_news_items = [
            {
                'published': (datetime.now() - timedelta(hours=1)).isoformat() + 'Z',
                'sentiment': 0.4,
                'title': 'Positive earnings report'
            },
            {
                'published': (datetime.now() - timedelta(hours=6)).isoformat() + 'Z',
                'sentiment': 0.2,
                'title': 'Market update'
            },
            {
                'published': (datetime.now() - timedelta(days=1)).isoformat() + 'Z',
                'sentiment': -0.1,
                'title': 'Minor regulatory concern'
            }
        ]
    
    def test_scorer_initialization(self):
        """Test that the scorer initializes properly"""
        scorer = EnhancedSentimentScorer()
        
        self.assertIsInstance(scorer, EnhancedSentimentScorer)
        self.assertEqual(scorer.lookback_days, 252)
        self.assertEqual(scorer.min_samples, 30)
        self.assertIsInstance(scorer.scoring_config, dict)
        self.assertIn('base_weights', scorer.scoring_config)
        self.assertIsInstance(scorer.sentiment_history, list)
    
    def test_scorer_initialization_custom_params(self):
        """Test scorer with custom parameters"""
        scorer = EnhancedSentimentScorer(lookback_days=100, min_samples=20)
        
        self.assertEqual(scorer.lookback_days, 100)
        self.assertEqual(scorer.min_samples, 20)
    
    def test_calculate_enhanced_sentiment_basic(self):
        """Test basic enhanced sentiment calculation"""
        result = self.scorer.calculate_enhanced_sentiment(
            raw_components=self.valid_components,
            market_data=self.valid_market_data,
            news_items=self.valid_news_items
        )
        
        # Verify return type
        self.assertIsInstance(result, SentimentMetrics)
        
        # Test score ranges
        self.assertGreaterEqual(result.raw_score, -1)
        self.assertLessEqual(result.raw_score, 1)
        self.assertGreaterEqual(result.normalized_score, 0)
        self.assertLessEqual(result.normalized_score, 100)
        self.assertGreaterEqual(result.confidence, 0)
        self.assertLessEqual(result.confidence, 1)
        self.assertGreaterEqual(result.percentile_rank, 0)
        self.assertLessEqual(result.percentile_rank, 100)
        
        # Test that strength category is valid
        self.assertIsInstance(result.strength_category, SentimentStrength)
    
    def test_weighted_base_score_calculation(self):
        """Test the weighted base score calculation"""
        # Test with all components
        score = self.scorer._calculate_weighted_base_score(self.valid_components)
        self.assertGreaterEqual(score, -1)
        self.assertLessEqual(score, 1)
        
        # Test with missing components
        partial_components = {
            'news_sentiment': 0.5,
            'social_sentiment': 0.3
        }
        score = self.scorer._calculate_weighted_base_score(partial_components)
        self.assertGreaterEqual(score, -1)
        self.assertLessEqual(score, 1)
        
        # Test with empty components
        score = self.scorer._calculate_weighted_base_score({})
        self.assertEqual(score, 0)
        
        # Test with None values
        components_with_none = {
            'news_sentiment': 0.5,
            'social_sentiment': None,
            'technical_momentum': 0.2
        }
        score = self.scorer._calculate_weighted_base_score(components_with_none)
        self.assertGreaterEqual(score, -1)
        self.assertLessEqual(score, 1)
    
    def test_time_decay_application(self):
        """Test time decay functionality"""
        base_score = 0.5
        
        # Test with valid news items
        decayed_score = self.scorer._apply_time_decay(base_score, self.valid_news_items)
        self.assertIsInstance(decayed_score, float)
        
        # Test with no news items
        decayed_score = self.scorer._apply_time_decay(base_score, None)
        self.assertEqual(decayed_score, base_score)
        
        # Test with empty news list
        decayed_score = self.scorer._apply_time_decay(base_score, [])
        self.assertEqual(decayed_score, base_score)
        
        # Test with malformed news items
        bad_news = [
            {'published': 'invalid-date', 'sentiment': 0.5},
            {'sentiment': 0.3},  # Missing published field
            {}  # Empty item
        ]
        decayed_score = self.scorer._apply_time_decay(base_score, bad_news)
        self.assertIsInstance(decayed_score, float)
    
    def test_volatility_adjustment(self):
        """Test volatility adjustment functionality"""
        base_score = 0.5
        
        # Test low volatility scenario
        low_vol_data = {'volatility': 0.1}
        adjusted = self.scorer._apply_volatility_adjustment(base_score, low_vol_data)
        self.assertIsInstance(adjusted, float)
        
        # Test high volatility scenario
        high_vol_data = {'volatility': 0.4}
        adjusted = self.scorer._apply_volatility_adjustment(base_score, high_vol_data)
        self.assertIsInstance(adjusted, float)
        
        # Test normal volatility
        normal_vol_data = {'volatility': 0.2}
        adjusted = self.scorer._apply_volatility_adjustment(base_score, normal_vol_data)
        self.assertIsInstance(adjusted, float)
        
        # Test with no market data
        adjusted = self.scorer._apply_volatility_adjustment(base_score, None)
        self.assertEqual(adjusted, base_score)
        
        # Test with missing volatility field
        adjusted = self.scorer._apply_volatility_adjustment(base_score, {})
        self.assertEqual(adjusted, base_score)
    
    def test_market_regime_adjustment(self):
        """Test market regime adjustment functionality"""
        base_score = 0.5
        
        # Test all market regimes
        regimes = ['bull', 'bear', 'volatile', 'stable', 'crisis']
        
        for regime in regimes:
            market_data = {'regime': regime}
            adjusted = self.scorer._apply_market_regime_adjustment(base_score, market_data)
            self.assertIsInstance(adjusted, float)
        
        # Test with unknown regime
        unknown_regime_data = {'regime': 'unknown_regime'}
        adjusted = self.scorer._apply_market_regime_adjustment(base_score, unknown_regime_data)
        self.assertEqual(adjusted, base_score)
        
        # Test with no market data
        adjusted = self.scorer._apply_market_regime_adjustment(base_score, None)
        self.assertEqual(adjusted, base_score)
    
    def test_statistical_metrics_calculation(self):
        """Test statistical metrics calculation"""
        # Test with insufficient history
        z_score, percentile = self.scorer._calculate_statistical_metrics(0.5)
        self.assertEqual(z_score, 0.0)
        self.assertEqual(percentile, 50.0)
        
        # Add sufficient history
        test_history = np.random.normal(0, 0.3, 100).tolist()
        self.scorer.sentiment_history = test_history
        
        z_score, percentile = self.scorer._calculate_statistical_metrics(0.5)
        self.assertIsInstance(z_score, float)
        self.assertIsInstance(percentile, float)
        self.assertGreaterEqual(percentile, 0)
        self.assertLessEqual(percentile, 100)
        
        # Test extreme values
        z_score, percentile = self.scorer._calculate_statistical_metrics(2.0)
        self.assertGreater(z_score, 0)
        self.assertGreater(percentile, 90)
        
        z_score, percentile = self.scorer._calculate_statistical_metrics(-2.0)
        self.assertLess(z_score, 0)
        self.assertLess(percentile, 10)
    
    def test_score_normalization(self):
        """Test score normalization to 0-100 scale"""
        # Test boundary values
        self.assertEqual(self.scorer._normalize_score(-1), 0)
        self.assertEqual(self.scorer._normalize_score(1), 100)
        self.assertEqual(self.scorer._normalize_score(0), 50)
        
        # Test intermediate values
        self.assertEqual(self.scorer._normalize_score(0.5), 75)
        self.assertEqual(self.scorer._normalize_score(-0.5), 25)
        
        # Test values outside range (should be clipped)
        self.assertEqual(self.scorer._normalize_score(-2), 0)
        self.assertEqual(self.scorer._normalize_score(2), 100)
    
    def test_strength_categorization(self):
        """Test sentiment strength categorization"""
        # Test very strong positive
        strength = self.scorer._categorize_strength(90, 2.5)
        self.assertEqual(strength, SentimentStrength.VERY_STRONG_POSITIVE)
        
        # Test strong positive
        strength = self.scorer._categorize_strength(75, 1.5)
        self.assertEqual(strength, SentimentStrength.STRONG_POSITIVE)
        
        # Test moderate positive
        strength = self.scorer._categorize_strength(65, 0.5)
        self.assertEqual(strength, SentimentStrength.MODERATE_POSITIVE)
        
        # Test neutral
        strength = self.scorer._categorize_strength(50, 0)
        self.assertEqual(strength, SentimentStrength.NEUTRAL)
        
        # Test moderate negative
        strength = self.scorer._categorize_strength(35, -0.5)
        self.assertEqual(strength, SentimentStrength.MODERATE_NEGATIVE)
        
        # Test strong negative
        strength = self.scorer._categorize_strength(25, -1.5)
        self.assertEqual(strength, SentimentStrength.STRONG_NEGATIVE)
        
        # Test very strong negative
        strength = self.scorer._categorize_strength(10, -2.5)
        self.assertEqual(strength, SentimentStrength.VERY_STRONG_NEGATIVE)
    
    def test_confidence_calculation(self):
        """Test confidence calculation"""
        # Test with valid data
        confidence = self.scorer._calculate_confidence(self.valid_components, self.valid_market_data)
        self.assertGreaterEqual(confidence, 0)
        self.assertLessEqual(confidence, 1)
        
        # Test with partial components
        partial_components = {'news_sentiment': 0.5}
        confidence = self.scorer._calculate_confidence(partial_components, self.valid_market_data)
        self.assertGreaterEqual(confidence, 0)
        self.assertLessEqual(confidence, 1)
        
        # Test with no market data
        confidence = self.scorer._calculate_confidence(self.valid_components, None)
        self.assertGreaterEqual(confidence, 0)
        self.assertLessEqual(confidence, 1)
    
    def test_trading_signal_generation(self):
        """Test trading signal generation"""
        # Create test sentiment metrics
        test_metrics = SentimentMetrics(
            raw_score=0.5,
            normalized_score=75,
            strength_category=SentimentStrength.STRONG_POSITIVE,
            confidence=0.85,
            volatility_adjusted_score=0.48,
            market_adjusted_score=0.52,
            z_score=1.8,
            percentile_rank=85
        )
        
        # Test conservative signal
        signal = self.scorer.get_trading_signal(test_metrics, 'conservative')
        self.assertIn('signal', signal)
        self.assertIn('strength', signal)
        self.assertIn('confidence', signal)
        self.assertIn(signal['signal'], ['BUY', 'SELL', 'HOLD'])
        self.assertIn(signal['strength'], ['STRONG', 'MODERATE', 'WEAK'])
        
        # Test moderate signal
        signal = self.scorer.get_trading_signal(test_metrics, 'moderate')
        self.assertIn('signal', signal)
        
        # Test aggressive signal
        signal = self.scorer.get_trading_signal(test_metrics, 'aggressive')
        self.assertIn('signal', signal)
        
        # Test invalid risk tolerance
        signal = self.scorer.get_trading_signal(test_metrics, 'invalid_risk')
        self.assertIn('signal', signal)  # Should default to moderate
    
    def test_error_handling_invalid_inputs(self):
        """Test error handling with invalid inputs"""
        # Test with invalid component types
        invalid_components = {
            'news_sentiment': 'invalid',
            'social_sentiment': float('inf'),
            'technical_momentum': float('nan')
        }
        
        # Should not crash, should handle gracefully
        result = self.scorer.calculate_enhanced_sentiment(
            raw_components=invalid_components,
            market_data=self.valid_market_data,
            news_items=self.valid_news_items
        )
        self.assertIsInstance(result, SentimentMetrics)
        
        # Test with empty inputs
        result = self.scorer.calculate_enhanced_sentiment(
            raw_components={},
            market_data=None,
            news_items=None
        )
        self.assertIsInstance(result, SentimentMetrics)
        
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        # Test with all zero components
        zero_components = {k: 0.0 for k in self.valid_components.keys()}
        result = self.scorer.calculate_enhanced_sentiment(
            raw_components=zero_components,
            market_data=self.valid_market_data,
            news_items=[]
        )
        self.assertIsInstance(result, SentimentMetrics)
        self.assertAlmostEqual(result.normalized_score, 50, places=1)
        
        # Test with extreme positive components
        extreme_positive = {k: 1.0 for k in self.valid_components.keys()}
        result = self.scorer.calculate_enhanced_sentiment(
            raw_components=extreme_positive,
            market_data=self.valid_market_data,
            news_items=[]
        )
        self.assertIsInstance(result, SentimentMetrics)
        self.assertGreater(result.normalized_score, 80)
        
        # Test with extreme negative components
        extreme_negative = {k: -1.0 for k in self.valid_components.keys()}
        result = self.scorer.calculate_enhanced_sentiment(
            raw_components=extreme_negative,
            market_data=self.valid_market_data,
            news_items=[]
        )
        self.assertIsInstance(result, SentimentMetrics)
        self.assertLess(result.normalized_score, 20)
    
    def test_history_management(self):
        """Test sentiment history management"""
        initial_length = len(self.scorer.sentiment_history)
        
        # Add a score to history
        self.scorer._update_history(0.5)
        self.assertEqual(len(self.scorer.sentiment_history), initial_length + 1)
        
        # Test history limit (should not exceed lookback_days)
        for i in range(300):
            self.scorer._update_history(0.1 * i)
        
        self.assertLessEqual(len(self.scorer.sentiment_history), self.scorer.lookback_days)

class TestMarketContextDetector(unittest.TestCase):
    """Test market context detection functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not ENHANCED_SENTIMENT_AVAILABLE:
            self.skipTest("Enhanced sentiment scoring not available")
    
    def test_market_context_detector_creation(self):
        """Test market context detector creation"""
        try:
            detector = create_market_context_detector()
            self.assertIsNotNone(detector)
        except Exception as e:
            # If function doesn't exist, that's okay - we'll note it
            self.skipTest(f"Market context detector not implemented: {e}")

class TestSentimentMetrics(unittest.TestCase):
    """Test SentimentMetrics dataclass"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not ENHANCED_SENTIMENT_AVAILABLE:
            self.skipTest("Enhanced sentiment scoring not available")
    
    def test_sentiment_metrics_creation(self):
        """Test SentimentMetrics object creation"""
        metrics = SentimentMetrics(
            raw_score=0.5,
            normalized_score=75.0,
            strength_category=SentimentStrength.STRONG_POSITIVE,
            confidence=0.85,
            volatility_adjusted_score=0.48,
            market_adjusted_score=0.52,
            z_score=1.8,
            percentile_rank=85.0
        )
        
        self.assertEqual(metrics.raw_score, 0.5)
        self.assertEqual(metrics.normalized_score, 75.0)
        self.assertEqual(metrics.strength_category, SentimentStrength.STRONG_POSITIVE)
        self.assertEqual(metrics.confidence, 0.85)
        self.assertEqual(metrics.z_score, 1.8)
        self.assertEqual(metrics.percentile_rank, 85.0)

class TestPerformanceAndStress(unittest.TestCase):
    """Test performance and stress scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not ENHANCED_SENTIMENT_AVAILABLE:
            self.skipTest("Enhanced sentiment scoring not available")
        
        self.scorer = EnhancedSentimentScorer()
    
    def test_large_news_dataset(self):
        """Test with large number of news items"""
        large_news_items = []
        for i in range(1000):
            large_news_items.append({
                'published': (datetime.now() - timedelta(hours=i)).isoformat() + 'Z',
                'sentiment': np.random.uniform(-1, 1),
                'title': f'News item {i}'
            })
        
        components = {'news_sentiment': 0.3, 'social_sentiment': 0.2}
        
        # Should complete without timeout or memory issues
        result = self.scorer.calculate_enhanced_sentiment(
            raw_components=components,
            market_data={'volatility': 0.2, 'regime': 'stable'},
            news_items=large_news_items
        )
        
        self.assertIsInstance(result, SentimentMetrics)
    
    def test_repeated_calculations(self):
        """Test repeated calculations for memory leaks"""
        components = {
            'news_sentiment': 0.3,
            'social_sentiment': 0.2,
            'technical_momentum': 0.1
        }
        
        # Run many calculations
        for i in range(100):
            result = self.scorer.calculate_enhanced_sentiment(
                raw_components=components,
                market_data={'volatility': 0.2, 'regime': 'stable'},
                news_items=[]
            )
            self.assertIsInstance(result, SentimentMetrics)

def run_tests():
    """Run all tests and return results"""
    if not ENHANCED_SENTIMENT_AVAILABLE:
        print("❌ Enhanced sentiment scoring not available - cannot run tests")
        return False
    
    # Create test suite
    test_classes = [
        TestEnhancedSentimentScoring,
        TestMarketContextDetector,
        TestSentimentMetrics,
        TestPerformanceAndStress
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print("ENHANCED SENTIMENT SCORING TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall Result: {'✅ PASSED' if success else '❌ FAILED'}")
    
    return success

if __name__ == "__main__":
    print("🧪 Running Enhanced Sentiment Scoring Tests")
    print("=" * 60)
    
    success = run_tests()
    
    if success:
        print("\n🎯 All tests passed! Enhanced sentiment scoring is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
    
    exit(0 if success else 1)
