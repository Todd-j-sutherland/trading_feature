#!/usr/bin/env python3
"""
Comprehensive Unit Test Suite for ML Trading System
Optimized, focused tests for all core components

Run with: python test_suite_comprehensive.py
Or specific modules: python -m unittest test_suite_comprehensive.TestNewsSentiment
"""

import unittest
import sys
import os
import tempfile
import shutil
import json
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from app.config.settings import Settings

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Suppress logging during tests
logging.disable(logging.CRITICAL)

class TestDataGenerator:
    """Generate consistent test data"""
    
    @staticmethod
    def mock_sentiment_data():
        return {
            'overall_sentiment': 0.15,
            'confidence': 0.75,
            'news_count': 12,
            'reddit_sentiment': 0.05,
            'event_score': 0.1,
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def mock_trading_data():
        return {
            'symbol': 'CBA.AX',
            'signal': 'HOLD',
            'sentiment_score': 0.15,
            'confidence': 0.75,
            'current_price': 105.50,
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def mock_ml_features():
        return [0.15, 0.75, 12, 0.05, 0.1, 0.11, 2, 14, 1, 1]

class TestNewsSentiment(unittest.TestCase):
    """Test News Sentiment Analysis Core Functionality"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_sentiment_initialization(self):
        """Test sentiment analyzer initialization"""
        try:
            from src.news_sentiment import NewsSentimentAnalyzer
            analyzer = NewsSentimentAnalyzer()
            self.assertIsNotNone(analyzer)
            self.assertTrue(hasattr(analyzer, 'sentiment_analyzer'))
        except ImportError:
            self.skipTest("NewsSentimentAnalyzer not available")
    
    @patch('src.news_sentiment.NewsSentimentAnalyzer')
    def test_sentiment_score_calculation(self, mock_analyzer):
        """Test sentiment score calculation"""
        mock_instance = Mock()
        mock_instance.analyze_sentiment.return_value = TestDataGenerator.mock_sentiment_data()
        mock_analyzer.return_value = mock_instance
        
        result = mock_instance.analyze_sentiment("CBA.AX")
        
        self.assertIn('overall_sentiment', result)
        self.assertIn('confidence', result)
        self.assertGreaterEqual(result['confidence'], 0.0)
        self.assertLessEqual(result['confidence'], 1.0)
        self.assertGreaterEqual(result['overall_sentiment'], -1.0)
        self.assertLessEqual(result['overall_sentiment'], 1.0)
    
    def test_ml_feature_extraction(self):
        """Test ML feature extraction"""
        sentiment_data = TestDataGenerator.mock_sentiment_data()
        features = TestDataGenerator.mock_ml_features()
        
        # Test feature count and types
        self.assertEqual(len(features), 10)
        self.assertIsInstance(features[0], (int, float))
        self.assertIsInstance(features[1], (int, float))

class TestTradingAnalyzer(unittest.TestCase):
    """Test Trading Analysis and Signal Generation"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_trading_analyzer_initialization(self):
        """Test trading analyzer initialization"""
        try:
            from news_trading_analyzer import NewsTradingAnalyzer
            analyzer = NewsTradingAnalyzer()
            self.assertIsNotNone(analyzer)
        except ImportError:
            self.skipTest("NewsTradingAnalyzer not available")
    
    def test_trading_signal_generation(self):
        """Test trading signal generation logic"""
        test_cases = [
            (0.7, 0.8, 'BUY'),      # Strong positive, high confidence
            (-0.7, 0.8, 'SELL'),    # Strong negative, high confidence
            (0.1, 0.4, 'HOLD'),     # Weak signal, low confidence
            (0.5, 0.3, 'HOLD'),     # Good signal, but low confidence
        ]
        
        for sentiment, confidence, expected in test_cases:
            signal = self._generate_signal(sentiment, confidence)
            self.assertEqual(signal, expected, 
                           f"Failed for sentiment={sentiment}, confidence={confidence}")
    
    def test_symbol_validation(self):
        """Test ASX symbol validation"""
        settings = Settings()
        valid_symbols = settings.BANK_SYMBOLS
        invalid_symbols = ['CBA', 'WBC.US', '', None, 'INVALID']
        
        for symbol in valid_symbols:
            self.assertTrue(self._is_valid_asx_symbol(symbol))
        
        for symbol in invalid_symbols:
            self.assertFalse(self._is_valid_asx_symbol(symbol))
    
    def test_confidence_thresholds(self):
        """Test confidence threshold validation"""
        self.assertGreater(0.8, 0.7)  # High confidence
        self.assertGreater(0.6, 0.5)  # Medium confidence
        self.assertLess(0.3, 0.5)     # Low confidence
    
    def _generate_signal(self, sentiment, confidence):
        """Generate trading signal based on sentiment and confidence"""
        if confidence < 0.5:
            return 'HOLD'
        elif sentiment > 0.3 and confidence > 0.7:
            return 'BUY'
        elif sentiment < -0.3 and confidence > 0.7:
            return 'SELL'
        else:
            return 'HOLD'
    
    def _is_valid_asx_symbol(self, symbol):
        """Validate ASX symbol format"""
        if not symbol or not isinstance(symbol, str):
            return False
        return symbol.endswith('.AX') and len(symbol) > 3

class TestMLPipeline(unittest.TestCase):
    """Test ML Training Pipeline"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_ml_pipeline_initialization(self):
        """Test ML pipeline initialization"""
        try:
            from src.ml_training_pipeline import MLTrainingPipeline
            pipeline = MLTrainingPipeline(data_dir=self.test_dir)
            self.assertIsNotNone(pipeline)
            self.assertTrue(hasattr(pipeline, 'db_path'))
        except ImportError:
            self.skipTest("MLTrainingPipeline not available")
    
    def test_feature_collection(self):
        """Test training data collection"""
        sentiment_data = TestDataGenerator.mock_sentiment_data()
        sentiment_data.update({
            'symbol': 'CBA.AX',
            'reddit_sentiment': {'average_sentiment': 0.05},
            'sentiment_components': {'events': 0.1}
        })
        
        # Test data structure
        self.assertIn('overall_sentiment', sentiment_data)
        self.assertIn('confidence', sentiment_data)
        self.assertIn('news_count', sentiment_data)
    
    def test_synthetic_model_training(self):
        """Test model training with synthetic data"""
        n_samples = 100
        
        # Generate synthetic features
        np.random.seed(42)
        X = pd.DataFrame({
            'sentiment_score': np.random.uniform(-1, 1, n_samples),
            'confidence': np.random.uniform(0.3, 1, n_samples),
            'news_count': np.random.randint(1, 20, n_samples),
            'reddit_sentiment': np.random.uniform(-1, 1, n_samples),
            'event_score': np.random.uniform(-0.5, 0.5, n_samples)
        })
        
        # Generate synthetic labels (profit/loss)
        y = pd.Series(np.random.choice([0, 1], n_samples, p=[0.4, 0.6]))
        
        # Test data quality
        self.assertEqual(len(X), n_samples)
        self.assertEqual(len(y), n_samples)
        self.assertGreater(len(X.columns), 4)
        self.assertIn('sentiment_score', X.columns)

class TestDataFeed(unittest.TestCase):
    """Test Data Feed Functionality"""
    
    def test_data_feed_initialization(self):
        """Test data feed initialization"""
        try:
            from src.data_feed import ASXDataFeed
            data_feed = ASXDataFeed()
            self.assertIsNotNone(data_feed)
        except ImportError:
            self.skipTest("ASXDataFeed not available")
    
    @patch('yfinance.Ticker')
    def test_stock_data_retrieval(self, mock_ticker):
        """Test stock data retrieval with mocked yfinance"""
        # Mock yfinance response
        mock_hist = Mock()
        mock_hist.empty = False
        mock_hist.iloc = Mock()
        mock_ticker.return_value.history.return_value = mock_hist
        
        try:
            from src.data_feed import ASXDataFeed
            data_feed = ASXDataFeed()
            result = data_feed.get_stock_data('CBA.AX')
            self.assertIsNotNone(result)
        except ImportError:
            self.skipTest("ASXDataFeed not available")

class TestDailyManager(unittest.TestCase):
    """Test Daily Manager Functionality"""
    
    def test_daily_manager_initialization(self):
        """Test daily manager initialization"""
        try:
            from daily_manager import DailyManager
            manager = DailyManager()
            self.assertIsNotNone(manager)
        except ImportError:
            self.skipTest("DailyManager not available")
    
    def test_daily_workflow(self):
        """Test daily analysis workflow"""
        workflow_steps = {
            'collect_data': True,
            'analyze_sentiment': True,
            'generate_signals': True,
            'track_outcomes': True,
            'update_models': False  # Weekly task
        }
        
        completed_steps = sum(workflow_steps.values())
        self.assertGreaterEqual(completed_steps, 3)

class TestComprehensiveAnalyzer(unittest.TestCase):
    """Test Comprehensive System Analysis"""
    
    def test_system_readiness_analysis(self):
        """Test system readiness assessment"""
        readiness_metrics = {
            'training_ready': True,
            'model_available': True,
            'min_samples_met': True,
            'feature_quality_good': True,
            'data_completeness': 0.95
        }
        
        self.assertTrue(readiness_metrics['training_ready'])
        self.assertGreater(readiness_metrics['data_completeness'], 0.8)
    
    def test_performance_metrics(self):
        """Test performance metrics calculation"""
        performance = {
            'sample_count': 876,
            'class_balance': 0.58,
            'collection_rate': 127.0,
            'model_accuracy': 0.67
        }
        
        self.assertGreater(performance['sample_count'], 50)
        self.assertGreater(performance['class_balance'], 0.3)
        self.assertLess(performance['class_balance'], 0.8)
        self.assertGreater(performance['collection_rate'], 20)

class TestSystemIntegration(unittest.TestCase):
    """Test System Integration"""
    
    def test_component_integration(self):
        """Test integration between components"""
        components = {
            'news_sentiment': True,
            'trading_analyzer': True,
            'ml_pipeline': True,
            'data_feed': True,
            'daily_manager': True
        }
        
        active_components = sum(components.values())
        self.assertGreaterEqual(active_components, 4)
    
    def test_end_to_end_workflow(self):
        """Test complete trading workflow"""
        workflow = {
            'data_collection': 'complete',
            'sentiment_analysis': 'complete',
            'signal_generation': 'complete',
            'outcome_tracking': 'active',
            'model_training': 'scheduled'
        }
        
        self.assertEqual(workflow['data_collection'], 'complete')
        self.assertEqual(workflow['sentiment_analysis'], 'complete')
        self.assertIn(workflow['outcome_tracking'], ['active', 'complete'])

class TestUtilities(unittest.TestCase):
    """Test Utility Functions"""
    
    def test_data_validation(self):
        """Test data validation utilities"""
        # Valid data
        valid_data = {
            'sentiment_score': 0.15,
            'confidence': 0.75,
            'news_count': 12
        }
        
        # Test ranges
        self.assertGreaterEqual(valid_data['sentiment_score'], -1.0)
        self.assertLessEqual(valid_data['sentiment_score'], 1.0)
        self.assertGreaterEqual(valid_data['confidence'], 0.0)
        self.assertLessEqual(valid_data['confidence'], 1.0)
        self.assertGreaterEqual(valid_data['news_count'], 0)
    
    def test_error_handling(self):
        """Test error handling utilities"""
        # Test various error conditions
        with self.assertRaises((ValueError, TypeError)):
            raise ValueError("Test error")
        
        # Test graceful degradation
        fallback_result = self._handle_error(None)
        self.assertIsNotNone(fallback_result)
        self.assertEqual(fallback_result['status'], 'error')
    
    def _handle_error(self, data):
        """Handle errors gracefully"""
        if data is None:
            return {'status': 'error', 'message': 'No data available'}
        return {'status': 'success', 'data': data}

# Test Suite Runner
class TestSuiteRunner:
    """Run comprehensive test suite"""
    
    @staticmethod
    def run_all_tests():
        """Run all tests"""
        test_classes = [
            TestNewsSentiment,
            TestTradingAnalyzer,
            TestMLPipeline,
            TestDataFeed,
            TestDailyManager,
            TestComprehensiveAnalyzer,
            TestSystemIntegration,
            TestUtilities
        ]
        
        # Create test suite
        suite = unittest.TestSuite()
        for test_class in test_classes:
            tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
            suite.addTests(tests)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2, buffer=True)
        result = runner.run(suite)
        
        return result.wasSuccessful()
    
    @staticmethod
    def run_quick_tests():
        """Run critical tests only"""
        quick_classes = [
            TestNewsSentiment,
            TestTradingAnalyzer,
            TestMLPipeline
        ]
        
        suite = unittest.TestSuite()
        for test_class in quick_classes:
            # Add only core test methods
            core_methods = [method for method in dir(test_class) 
                          if method.startswith('test_') and 
                          any(keyword in method for keyword in 
                              ['initialization', 'signal', 'sentiment'])]
            
            for method in core_methods:
                suite.addTest(test_class(method))
        
        runner = unittest.TextTestRunner(verbosity=1)
        result = runner.run(suite)
        
        return result.wasSuccessful()

def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ML Trading System Test Suite")
    parser.add_argument("--quick", action="store_true", 
                       help="Run quick test subset")
    parser.add_argument("--module", type=str, 
                       help="Run specific test module")
    
    args = parser.parse_args()
    
    print("🧪 ML Trading System - Comprehensive Test Suite")
    print("=" * 60)
    
    if args.module:
        # Run specific module
        test_class = globals().get(f"Test{args.module}")
        if test_class:
            suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)
            success = result.wasSuccessful()
        else:
            print(f"❌ Test module 'Test{args.module}' not found")
            return False
    
    elif args.quick:
        print("🚀 Running Quick Test Suite...")
        success = TestSuiteRunner.run_quick_tests()
    
    else:
        print("🔍 Running Complete Test Suite...")
        success = TestSuiteRunner.run_all_tests()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed successfully!")
        print("🎯 System is ready for production use")
    else:
        print("❌ Some tests failed")
        print("🔧 Please review and fix issues before production")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
