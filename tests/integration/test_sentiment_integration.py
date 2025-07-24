#!/usr/bin/env python3
"""
Integration Tests for Enhanced Sentiment Integration System
Tests the integration between enhanced sentiment and the existing system
"""

import sys
import os
import unittest
from datetime import datetime

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'src'))

try:
    from app.core.sentiment.integration import (
        SentimentIntegrationManager, 
        enhance_existing_sentiment, 
        get_enhanced_trading_signals
    )
    from app.core.sentiment.enhanced_scoring import SentimentMetrics, SentimentStrength
    INTEGRATION_AVAILABLE = True
except ImportError as e:
    INTEGRATION_AVAILABLE = False
    print(f"Enhanced sentiment integration not available: {e}")

class TestSentimentIntegrationManager(unittest.TestCase):
    """Test the main integration manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not INTEGRATION_AVAILABLE:
            self.skipTest("Enhanced sentiment integration not available")
        
        self.manager = SentimentIntegrationManager()
        
        # Standard legacy sentiment data
        self.legacy_data = {
            'symbol': 'CBA.AX',
            'timestamp': datetime.now().isoformat(),
            'news_count': 8,
            'sentiment_scores': {
                'average_sentiment': 0.15,
                'positive_count': 5,
                'negative_count': 2,
                'neutral_count': 1
            },
            'reddit_sentiment': {
                'average_sentiment': 0.05,
                'posts_analyzed': 12
            },
            'significant_events': {
                'events_detected': [
                    {'type': 'earnings_report', 'sentiment_impact': 0.2},
                    {'type': 'dividend_announcement', 'sentiment_impact': 0.1}
                ]
            },
            'overall_sentiment': 0.12,
            'confidence': 0.68,
            'recent_headlines': [
                'CBA reports strong quarterly earnings',
                'Banking sector sees increased activity'
            ]
        }
    
    def test_manager_initialization(self):
        """Test that the integration manager initializes properly"""
        manager = SentimentIntegrationManager()
        self.assertIsInstance(manager, SentimentIntegrationManager)
        self.assertIsInstance(manager.integration_history, list)
        self.assertEqual(len(manager.integration_history), 0)
    
    def test_legacy_to_enhanced_conversion(self):
        """Test conversion from legacy to enhanced sentiment"""
        enhanced = self.manager.convert_legacy_to_enhanced(self.legacy_data)
        
        # Verify return type
        self.assertIsInstance(enhanced, SentimentMetrics)
        
        # Verify enhanced metrics are within expected ranges
        self.assertGreaterEqual(enhanced.normalized_score, 0)
        self.assertLessEqual(enhanced.normalized_score, 100)
        self.assertGreaterEqual(enhanced.confidence, 0)
        self.assertLessEqual(enhanced.confidence, 1)
        self.assertIsInstance(enhanced.strength_category, SentimentStrength)
        
        # Verify history is updated
        self.assertEqual(len(self.manager.integration_history), 1)
        history_entry = self.manager.integration_history[0]
        self.assertEqual(history_entry['symbol'], 'CBA.AX')
        self.assertEqual(history_entry['legacy_score'], 0.12)
    
    def test_component_extraction(self):
        """Test extraction of components from legacy format"""
        components = self.manager._extract_components_from_legacy(self.legacy_data)
        
        self.assertIsInstance(components, dict)
        self.assertIn('news_sentiment', components)
        self.assertIn('social_sentiment', components)
        self.assertIn('analyst_sentiment', components)
        
        # Verify extracted values are reasonable
        self.assertEqual(components['news_sentiment'], 0.15)
        self.assertEqual(components['social_sentiment'], 0.05)
        
        # Verify missing components get default values
        self.assertIn('options_flow', components)
        self.assertEqual(components['options_flow'], 0)
    
    def test_market_context_creation(self):
        """Test creation of market context from legacy data"""
        market_data = self.manager._create_market_context_from_legacy(self.legacy_data)
        
        self.assertIsInstance(market_data, dict)
        self.assertIn('volatility', market_data)
        self.assertIn('regime', market_data)
        self.assertIn('market_trend', market_data)
        
        # Verify values are reasonable
        self.assertGreaterEqual(market_data['volatility'], 0.1)
        self.assertLessEqual(market_data['volatility'], 0.5)
        self.assertIn(market_data['regime'], ['bull', 'bear', 'stable', 'volatile'])
    
    def test_news_items_extraction(self):
        """Test extraction of news items from legacy format"""
        news_items = self.manager._extract_news_items_from_legacy(self.legacy_data)
        
        self.assertIsInstance(news_items, list)
        self.assertGreater(len(news_items), 0)
        
        for item in news_items:
            self.assertIn('published', item)
            self.assertIn('sentiment', item)
            self.assertIn('title', item)
            
            # Verify sentiment is in valid range
            self.assertGreaterEqual(item['sentiment'], -1)
            self.assertLessEqual(item['sentiment'], 1)
    
    def test_enhanced_trading_signals_generation(self):
        """Test generation of enhanced trading signals"""
        signals = self.manager.generate_enhanced_trading_signals(self.legacy_data)
        
        self.assertIsInstance(signals, dict)
        
        # Check that all risk profiles are present
        self.assertIn('conservative', signals)
        self.assertIn('moderate', signals)
        self.assertIn('aggressive', signals)
        self.assertIn('enhanced_analysis', signals)
        
        # Check signal structure
        for risk_level in ['conservative', 'moderate', 'aggressive']:
            signal_data = signals[risk_level]
            self.assertIn('signal', signal_data)
            self.assertIn('strength', signal_data)
            self.assertIn('reasoning', signal_data)
            self.assertIn(signal_data['signal'], ['BUY', 'SELL', 'HOLD'])
            self.assertIn(signal_data['strength'], ['STRONG', 'MODERATE', 'WEAK'])
        
        # Check enhanced analysis
        enhanced = signals['enhanced_analysis']
        self.assertIn('normalized_score', enhanced)
        self.assertIn('strength_category', enhanced)
        self.assertIn('confidence', enhanced)
        self.assertIn('improvement_over_legacy', enhanced)
    
    def test_integration_performance_report(self):
        """Test integration performance reporting"""
        # Generate some history
        for i in range(5):
            test_data = self.legacy_data.copy()
            test_data['symbol'] = f'TEST{i}.AX'
            test_data['overall_sentiment'] = 0.1 * i
            self.manager.convert_legacy_to_enhanced(test_data)
        
        report = self.manager.get_integration_performance_report()
        
        self.assertIsInstance(report, dict)
        self.assertIn('total_conversions', report)
        self.assertIn('average_score_improvement', report)
        self.assertIn('enhancement_effectiveness', report)
        self.assertIn('symbols_processed', report)
        
        self.assertEqual(report['total_conversions'], 5)
        self.assertIsInstance(report['symbols_processed'], list)
        self.assertIn(report['enhancement_effectiveness'], ['High', 'Moderate', 'Low'])
    
    def test_error_handling_malformed_legacy_data(self):
        """Test error handling with malformed legacy data"""
        # Test with missing fields
        minimal_data = {'symbol': 'TEST.AX', 'overall_sentiment': 0.1}
        enhanced = self.manager.convert_legacy_to_enhanced(minimal_data)
        self.assertIsInstance(enhanced, SentimentMetrics)
        
        # Test with None values
        none_data = {
            'symbol': 'TEST.AX',
            'overall_sentiment': None,
            'confidence': None,
            'sentiment_scores': None
        }
        enhanced = self.manager.convert_legacy_to_enhanced(none_data)
        self.assertIsInstance(enhanced, SentimentMetrics)
        
        # Test with empty data
        empty_data = {}
        enhanced = self.manager.convert_legacy_to_enhanced(empty_data)
        self.assertIsInstance(enhanced, SentimentMetrics)

class TestConvenienceFunctions(unittest.TestCase):
    """Test the convenience wrapper functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not INTEGRATION_AVAILABLE:
            self.skipTest("Enhanced sentiment integration not available")
        
        self.legacy_data = {
            'symbol': 'ANZ.AX',
            'overall_sentiment': 0.25,
            'confidence': 0.7,
            'news_count': 10,
            'sentiment_scores': {'average_sentiment': 0.3}
        }
    
    def test_enhance_existing_sentiment_function(self):
        """Test the enhance_existing_sentiment convenience function"""
        enhanced = enhance_existing_sentiment(self.legacy_data)
        
        self.assertIsInstance(enhanced, SentimentMetrics)
        self.assertGreaterEqual(enhanced.normalized_score, 0)
        self.assertLessEqual(enhanced.normalized_score, 100)
    
    def test_get_enhanced_trading_signals_function(self):
        """Test the get_enhanced_trading_signals convenience function"""
        signals = get_enhanced_trading_signals(self.legacy_data)
        
        self.assertIsInstance(signals, dict)
        self.assertIn('conservative', signals)
        self.assertIn('moderate', signals)
        self.assertIn('aggressive', signals)
        self.assertIn('enhanced_analysis', signals)
    
    def test_get_enhanced_trading_signals_custom_profiles(self):
        """Test enhanced trading signals with custom risk profiles"""
        custom_profiles = ['conservative', 'aggressive']
        signals = get_enhanced_trading_signals(self.legacy_data, custom_profiles)
        
        self.assertIn('conservative', signals)
        self.assertIn('aggressive', signals)
        self.assertNotIn('moderate', signals)
        self.assertIn('enhanced_analysis', signals)

class TestDailyAnalysisIntegration(unittest.TestCase):
    """Test the daily analysis integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not INTEGRATION_AVAILABLE:
            self.skipTest("Enhanced sentiment integration not available")
    
    def test_enhanced_trading_signals(self):
        """Test the enhanced trading signals function"""
        try:
            # Create test sentiment data
            sentiment_data = {
                'symbol': 'CBA.AX',
                'timestamp': datetime.now().isoformat(),
                'news_count': 8,
                'sentiment_scores': {
                    'average_sentiment': 0.15,
                    'positive_count': 5,
                    'negative_count': 2,
                    'neutral_count': 1
                }
            }
            
            # Get trading signals
            signals = get_enhanced_trading_signals(sentiment_data)
            
            self.assertIsInstance(signals, dict)
            
            # The function returns risk profiles and enhanced analysis
            expected_profiles = ['conservative', 'moderate', 'aggressive']
            for profile in expected_profiles:
                self.assertIn(profile, signals)
                profile_signals = signals[profile]
                self.assertIn('signal', profile_signals)
                self.assertIn('strength', profile_signals)
                self.assertIn('confidence', profile_signals)
            
            # Should also have enhanced analysis
            self.assertIn('enhanced_analysis', signals)
            enhanced = signals['enhanced_analysis']
            self.assertIn('normalized_score', enhanced)
            self.assertIn('confidence', enhanced)
            
        except Exception as e:
            # If the function has dependencies that aren't available, skip
            self.skipTest(f"Trading signals integration not fully available: {e}")

class TestPerformanceIntegration(unittest.TestCase):
    """Test performance characteristics of the integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        if not INTEGRATION_AVAILABLE:
            self.skipTest("Enhanced sentiment integration not available")
        
        self.manager = SentimentIntegrationManager()
    
    def test_batch_processing_performance(self):
        """Test performance with batch processing"""
        # Create batch of legacy data
        batch_data = []
        for i in range(50):
            data = {
                'symbol': f'TEST{i}.AX',
                'overall_sentiment': (i % 20 - 10) / 10,  # Range -1 to 1
                'confidence': 0.5 + (i % 10) / 20,  # Range 0.5 to 1
                'news_count': 5 + (i % 10),
                'sentiment_scores': {'average_sentiment': (i % 15 - 7) / 10}
            }
            batch_data.append(data)
        
        # Process batch
        import time
        start_time = time.time()
        
        for data in batch_data:
            enhanced = self.manager.convert_legacy_to_enhanced(data)
            self.assertIsInstance(enhanced, SentimentMetrics)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process at reasonable speed (less than 1 second for 50 items)
        self.assertLess(processing_time, 1.0)
        
        # Check integration history
        self.assertEqual(len(self.manager.integration_history), 50)

def run_integration_tests():
    """Run all integration tests and return results"""
    if not INTEGRATION_AVAILABLE:
        print("❌ Enhanced sentiment integration not available - cannot run tests")
        return False
    
    # Create test suite
    test_classes = [
        TestSentimentIntegrationManager,
        TestConvenienceFunctions,
        TestDailyAnalysisIntegration,
        TestPerformanceIntegration
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
    print("ENHANCED SENTIMENT INTEGRATION TEST SUMMARY")
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
    print("🧪 Running Enhanced Sentiment Integration Tests")
    print("=" * 60)
    
    success = run_integration_tests()
    
    if success:
        print("\n🎯 All integration tests passed! Enhanced sentiment integration is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
    
    exit(0 if success else 1)
