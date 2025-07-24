#!/usr/bin/env python3
"""
Comprehensive tests for NewsSentimentAnalyzer functionality
Tests all components including ML models, transformers, and database operations
"""

import unittest
import tempfile
import os
import sys
import json
import sqlite3
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.sentiment.news_analyzer import NewsSentimentAnalyzer
from app.core.data.collectors.news_collector import NewsCollector
from app.config.settings import Settings

class TestNewsSentimentAnalyzer(unittest.TestCase):
    """Test suite for NewsSentimentAnalyzer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, 'test_sentiment.db')
        
        # Mock settings to use temp directory
        self.mock_settings = Mock(spec=Settings)
        self.mock_settings.DATABASE_PATH = self.test_db_path
        self.mock_settings.NEWS_SOURCES = {
            'rss_feeds': {
                'test_feed': 'https://example.com/rss'
            }
        }
        
        # Sample news data for testing
        self.sample_news = [
            {
                'title': 'Commonwealth Bank reports strong quarterly earnings',
                'summary': 'CBA showed excellent performance with increased profits',
                'source': 'Test Source',
                'url': 'https://example.com/1',
                'published': datetime.now().isoformat(),
                'relevance': 'high'
            },
            {
                'title': 'Banking sector faces regulatory challenges',
                'summary': 'New regulations may impact bank profitability',
                'source': 'Test Source',
                'url': 'https://example.com/2',
                'published': datetime.now().isoformat(),
                'relevance': 'medium'
            },
            {
                'title': 'Westpac announces dividend increase',
                'summary': 'WBC shareholders to benefit from higher dividends',
                'source': 'Test Source',
                'url': 'https://example.com/3',
                'published': datetime.now().isoformat(),
                'relevance': 'high'
            }
        ]
        
        # Initialize analyzer with mocked dependencies
        with patch('app.core.sentiment.news_analyzer.Settings', return_value=self.mock_settings):
            self.analyzer = NewsSentimentAnalyzer()
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test analyzer initialization"""
        self.assertIsNotNone(self.analyzer)
        self.assertIsNotNone(self.analyzer.vader)
        self.assertIsNotNone(self.analyzer.bank_keywords)
        self.assertIn('CBA.AX', self.analyzer.bank_keywords)
        
    def test_bank_keywords_coverage(self):
        """Test that all major Australian banks are covered"""
        expected_banks = ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'MQG.AX', 'SUN.AX', 'QBE.AX']
        for bank in expected_banks:
            self.assertIn(bank, self.analyzer.bank_keywords, f"Missing keywords for {bank}")
            self.assertIsInstance(self.analyzer.bank_keywords[bank], list)
            self.assertGreater(len(self.analyzer.bank_keywords[bank]), 0)
    
    @patch('app.core.sentiment.news_analyzer.yf.Ticker')
    def test_fetch_yahoo_news(self, mock_ticker):
        """Test Yahoo Finance news fetching"""
        # Mock Yahoo Finance response
        mock_news_data = [
            {
                'title': 'Test News Title',
                'summary': 'Test news summary',
                'link': 'https://example.com/news',
                'providerPublishTime': datetime.now().timestamp()
            }
        ]
        
        mock_ticker_instance = Mock()
        mock_ticker_instance.news = mock_news_data
        mock_ticker.return_value = mock_ticker_instance
        
        # Test the method
        news = self.analyzer._fetch_yahoo_news('CBA.AX')
        
        self.assertIsInstance(news, list)
        if news:  # Only check if news was returned
            self.assertIn('title', news[0])
            self.assertIn('source', news[0])
            self.assertEqual(news[0]['source'], 'Yahoo Finance')
    
    def test_remove_duplicate_news(self):
        """Test duplicate news removal"""
        # Create news with duplicates
        news_with_duplicates = [
            {'title': 'Commonwealth Bank reports strong earnings', 'summary': 'Test'},
            {'title': 'Commonwealth Bank shows strong earnings results', 'summary': 'Test'},  # Similar
            {'title': 'Westpac announces dividend', 'summary': 'Test'},
            {'title': 'Different news entirely', 'summary': 'Test'}
        ]
        
        unique_news = self.analyzer._remove_duplicate_news(news_with_duplicates)
        
        # Should remove one duplicate
        self.assertLess(len(unique_news), len(news_with_duplicates))
        self.assertGreaterEqual(len(unique_news), 2)  # At least 2 unique items
    
    def test_ml_prediction_fallback_confidence(self):
        """Test the ML prediction fallback confidence calculation"""
        # Mock sentiment data
        sentiment_data = {
            'news_count': 5,
            'overall_sentiment': 0.3,
            'confidence': 0.6
        }
        
        # Mock ML model that fails predict_proba
        mock_model = Mock()
        mock_model.predict.return_value = [1]  # BUY signal
        mock_model.predict_proba.side_effect = Exception("predict_proba failed")
        
        self.analyzer.ml_model = mock_model
        self.analyzer.ml_feature_columns = ['sentiment_score', 'confidence', 'news_count']
        
        result = self.analyzer._get_ml_prediction(sentiment_data)
        
        # Check fallback confidence calculation
        self.assertIn('confidence', result)
        self.assertGreater(result['confidence'], 0.45)  # Base confidence
        self.assertLessEqual(result['confidence'], 0.75)  # Max confidence
        
        # Should include news count and sentiment boost
        expected_base = 0.45 + (min(5, 10) * 0.02)  # 0.45 + 0.10 = 0.55
        expected_boost = min(0.3 * 0.1, 0.1)  # 0.03
        expected_confidence = min(expected_base + expected_boost, 0.75)  # 0.58
        
        self.assertAlmostEqual(result['confidence'], expected_confidence, places=2)
    
    def test_confidence_calculation_with_no_news(self):
        """Test confidence calculation when no news is available"""
        sentiment_data = {
            'news_count': 0,
            'overall_sentiment': 0,
            'confidence': 0.5
        }
        
        # Mock ML model
        mock_model = Mock()
        mock_model.predict.return_value = [0]  # HOLD signal
        mock_model.predict_proba.side_effect = Exception("No data")
        
        self.analyzer.ml_model = mock_model
        self.analyzer.ml_feature_columns = ['sentiment_score', 'confidence', 'news_count']
        
        result = self.analyzer._get_ml_prediction(sentiment_data)
        
        # Should still provide a reasonable confidence (base minimum)
        self.assertEqual(result['confidence'], 0.45)  # Base confidence with no news
    
    def test_confidence_calculation_with_high_news_volume(self):
        """Test confidence calculation with high news volume"""
        sentiment_data = {
            'news_count': 15,  # More than 10 (capped)
            'overall_sentiment': 0.8,  # Strong sentiment
            'confidence': 0.7
        }
        
        mock_model = Mock()
        mock_model.predict.return_value = [1]
        mock_model.predict_proba.side_effect = Exception("Test fallback")
        
        self.analyzer.ml_model = mock_model
        self.analyzer.ml_feature_columns = ['sentiment_score', 'confidence', 'news_count']
        
        result = self.analyzer._get_ml_prediction(sentiment_data)
        
        # Should reach maximum confidence
        expected_base = 0.45 + (min(15, 10) * 0.02)  # 0.45 + 0.20 = 0.65
        expected_boost = min(0.8 * 0.1, 0.1)  # 0.08
        expected_confidence = min(expected_base + expected_boost, 0.75)  # 0.73, capped at 0.75
        
        self.assertAlmostEqual(result['confidence'], 0.73, places=2)
    
    def test_ml_trading_score_calculation(self):
        """Test ML trading score calculation"""
        market_data = {
            'market_volatility': 0.4,
            'market_trend': 'bullish',
            'trading_volume': 1.2
        }
        
        # Test with news items
        news_items = [
            {'title': 'Positive news', 'sentiment_analysis': {'composite': 0.5}},
            {'title': 'Negative news', 'sentiment_analysis': {'composite': -0.3}},
            {'title': 'Neutral news', 'sentiment_analysis': {'composite': 0.1}}
        ]
        
        result = self.analyzer._calculate_ml_trading_score(news_items, market_data)
        
        self.assertIn('ml_score', result)
        self.assertIn('confidence', result)
        self.assertIn('features', result)
        
        # Check features are calculated
        features = result['features']
        self.assertIn('avg_sentiment', features)
        self.assertIn('sentiment_variance', features)
        self.assertIn('news_count', features)
        self.assertEqual(features['news_count'], 3)
    
    def test_ml_trading_score_no_news(self):
        """Test ML trading score calculation with no news"""
        market_data = {
            'market_volatility': 0.5,
            'market_trend': 'neutral'
        }
        
        result = self.analyzer._calculate_ml_trading_score([], market_data)
        
        self.assertEqual(result['ml_score'], 0)
        self.assertGreater(result['confidence'], 0.3)  # Should have market-based confidence
        self.assertEqual(result['source'], 'market_conditions')
    
    def test_analyze_bank_sentiment_no_news(self):
        """Test sentiment analysis when no news is found"""
        with patch.object(self.analyzer, 'get_all_news', return_value=[]):
            result = self.analyzer.analyze_bank_sentiment('CBA.AX')
            
            self.assertEqual(result['symbol'], 'CBA.AX')
            self.assertEqual(result['news_count'], 0)
            self.assertEqual(result['overall_sentiment'], 0.0)
            self.assertEqual(result['confidence'], 0.0)
            self.assertIsInstance(result['timestamp'], str)
    
    def test_analyze_bank_sentiment_with_news(self):
        """Test sentiment analysis with sample news"""
        with patch.object(self.analyzer, 'get_all_news', return_value=self.sample_news):
            with patch.object(self.analyzer, '_analyze_news_sentiment') as mock_analyze:
                with patch.object(self.analyzer, '_get_reddit_sentiment') as mock_reddit:
                    with patch.object(self.analyzer, '_check_significant_events') as mock_events:
                        
                        # Mock return values
                        mock_analyze.return_value = {
                            'average_sentiment': 0.3,
                            'news_count': 3,
                            'sentiment_distribution': {'positive': 2, 'negative': 1, 'neutral': 0}
                        }
                        mock_reddit.return_value = {'average_sentiment': 0.2, 'posts_analyzed': 5}
                        mock_events.return_value = {'events_detected': []}
                        
                        result = self.analyzer.analyze_bank_sentiment('CBA.AX')
                        
                        self.assertEqual(result['symbol'], 'CBA.AX')
                        self.assertEqual(result['news_count'], 3)
                        self.assertNotEqual(result['overall_sentiment'], 0.0)
                        self.assertGreater(result['confidence'], 0.0)


class TestDatabaseOperations(unittest.TestCase):
    """Test database operations and data integrity"""
    
    def setUp(self):
        """Set up test database"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, 'test_trading.db')
        
    def tearDown(self):
        """Clean up test database"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_database_creation(self):
        """Test database creation and schema"""
        # Create database with standard schema
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Create sentiment history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sentiment_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                overall_sentiment REAL NOT NULL,
                confidence REAL NOT NULL,
                news_count INTEGER DEFAULT 0,
                ml_prediction TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create ML training data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ml_training_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                features TEXT NOT NULL,
                target REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        
        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        self.assertIn('sentiment_history', tables)
        self.assertIn('ml_training_data', tables)
        
        conn.close()
    
    def test_sentiment_data_insertion(self):
        """Test inserting sentiment data"""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Create table
        cursor.execute('''
            CREATE TABLE sentiment_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                overall_sentiment REAL NOT NULL,
                confidence REAL NOT NULL,
                news_count INTEGER DEFAULT 0
            )
        ''')
        
        # Insert test data
        test_data = [
            ('CBA.AX', datetime.now(), 0.45, 0.75, 5),
            ('WBC.AX', datetime.now(), -0.23, 0.68, 3),
            ('ANZ.AX', datetime.now(), 0.12, 0.71, 7)
        ]
        
        cursor.executemany(
            'INSERT INTO sentiment_history (symbol, timestamp, overall_sentiment, confidence, news_count) VALUES (?, ?, ?, ?, ?)',
            test_data
        )
        conn.commit()
        
        # Verify data was inserted
        cursor.execute('SELECT COUNT(*) FROM sentiment_history')
        count = cursor.fetchone()[0]
        self.assertEqual(count, 3)
        
        # Verify data integrity
        cursor.execute('SELECT symbol, overall_sentiment, confidence FROM sentiment_history WHERE symbol = ?', ('CBA.AX',))
        row = cursor.fetchone()
        self.assertEqual(row[0], 'CBA.AX')
        self.assertAlmostEqual(row[1], 0.45, places=2)
        self.assertAlmostEqual(row[2], 0.75, places=2)
        
        conn.close()
    
    def test_ml_training_data_storage(self):
        """Test ML training data storage and retrieval"""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Create table
        cursor.execute('''
            CREATE TABLE ml_training_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                features TEXT NOT NULL,
                target REAL NOT NULL
            )
        ''')
        
        # Test data
        features = {
            'sentiment_score': 0.3,
            'confidence': 0.7,
            'news_count': 5,
            'market_volatility': 0.4
        }
        
        cursor.execute(
            'INSERT INTO ml_training_data (symbol, timestamp, features, target) VALUES (?, ?, ?, ?)',
            ('CBA.AX', datetime.now(), json.dumps(features), 1.0)
        )
        conn.commit()
        
        # Retrieve and verify
        cursor.execute('SELECT features, target FROM ml_training_data WHERE symbol = ?', ('CBA.AX',))
        row = cursor.fetchone()
        
        retrieved_features = json.loads(row[0])
        self.assertEqual(retrieved_features['sentiment_score'], 0.3)
        self.assertEqual(retrieved_features['news_count'], 5)
        self.assertEqual(row[1], 1.0)
        
        conn.close()
    
    def test_database_transaction_rollback(self):
        """Test database transaction rollback on error"""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Create table
        cursor.execute('''
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        conn.commit()
        
        # Test transaction rollback
        try:
            conn.execute('BEGIN TRANSACTION')
            cursor.execute('INSERT INTO test_table (id, value) VALUES (1, "test1")')
            cursor.execute('INSERT INTO test_table (id, value) VALUES (1, "test2")')  # This should fail (duplicate ID)
            conn.commit()
        except sqlite3.IntegrityError:
            conn.rollback()
        
        # Verify no data was committed
        cursor.execute('SELECT COUNT(*) FROM test_table')
        count = cursor.fetchone()[0]
        self.assertEqual(count, 0)
        
        conn.close()


class TestNewsCollectorIntegration(unittest.TestCase):
    """Test news collector integration and error handling"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('app.core.sentiment.news_analyzer.requests.Session')
    def test_news_scraping_error_handling(self, mock_session):
        """Test error handling in news scraping"""
        # Mock session that raises exceptions
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        
        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        # Test that analyzer handles errors gracefully
        with patch('app.core.sentiment.news_analyzer.Settings') as mock_settings:
            mock_settings.return_value.NEWS_SOURCES = {'rss_feeds': {}}
            
            analyzer = NewsSentimentAnalyzer()
            
            # This should not raise an exception
            news = analyzer._scrape_news_sites('CBA.AX')
            self.assertIsInstance(news, list)  # Should return empty list on error
    
    def test_invalid_symbol_handling(self):
        """Test handling of invalid stock symbols"""
        with patch('app.core.sentiment.news_analyzer.Settings') as mock_settings:
            mock_settings.return_value.NEWS_SOURCES = {'rss_feeds': {}}
            
            analyzer = NewsSentimentAnalyzer()
            
            # Test with various invalid inputs
            invalid_symbols = [None, "", 123, [], {}]
            
            for invalid_symbol in invalid_symbols:
                try:
                    result = analyzer.get_all_news(["test"], invalid_symbol)
                    # Should handle gracefully and return empty list
                    self.assertIsInstance(result, list)
                except Exception as e:
                    # If exception is raised, it should be descriptive
                    self.assertIn("Symbol", str(e))


class TestMLModelIntegration(unittest.TestCase):
    """Test ML model loading and prediction"""
    
    def setUp(self):
        """Set up test environment with mock ML model"""
        self.temp_dir = tempfile.mkdtemp()
        self.model_dir = os.path.join(self.temp_dir, 'ml_models', 'models')
        os.makedirs(self.model_dir, exist_ok=True)
        
    def tearDown(self):
        """Clean up"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_ml_model_loading_failure(self):
        """Test ML model loading when files don't exist"""
        with patch('app.core.sentiment.news_analyzer.Settings') as mock_settings:
            mock_settings.return_value.NEWS_SOURCES = {'rss_feeds': {}}
            
            # Change working directory to temp dir so model files aren't found
            original_cwd = os.getcwd()
            os.chdir(self.temp_dir)
            
            try:
                analyzer = NewsSentimentAnalyzer()
                # Should handle missing model gracefully
                self.assertIsNone(analyzer.ml_model)
            finally:
                os.chdir(original_cwd)
    
    def test_ml_prediction_without_model(self):
        """Test ML prediction when no model is loaded"""
        with patch('app.core.sentiment.news_analyzer.Settings') as mock_settings:
            mock_settings.return_value.NEWS_SOURCES = {'rss_feeds': {}}
            
            analyzer = NewsSentimentAnalyzer()
            analyzer.ml_model = None  # Ensure no model
            
            sentiment_data = {'news_count': 5, 'overall_sentiment': 0.3}
            result = analyzer._get_ml_prediction(sentiment_data)
            
            self.assertEqual(result['prediction'], 'HOLD')
            self.assertEqual(result['confidence'], 0.0)
            self.assertIn('error', result)


class TestSystemIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_full_sentiment_analysis_pipeline(self):
        """Test the complete sentiment analysis pipeline"""
        with patch('app.core.sentiment.news_analyzer.Settings') as mock_settings:
            mock_settings.return_value.NEWS_SOURCES = {'rss_feeds': {}}
            mock_settings.return_value.DATABASE_PATH = os.path.join(self.temp_dir, 'test.db')
            
            analyzer = NewsSentimentAnalyzer()
            
            # Mock all external dependencies
            with patch.object(analyzer, 'get_all_news') as mock_get_news:
                with patch.object(analyzer, '_analyze_news_sentiment') as mock_analyze:
                    with patch.object(analyzer, '_get_reddit_sentiment') as mock_reddit:
                        with patch.object(analyzer, '_check_significant_events') as mock_events:
                            
                            # Set up mocks
                            mock_get_news.return_value = [
                                {'title': 'Test news', 'summary': 'Test summary', 'source': 'Test'}
                            ]
                            mock_analyze.return_value = {
                                'average_sentiment': 0.3,
                                'news_count': 1,
                                'sentiment_distribution': {'positive': 1, 'negative': 0, 'neutral': 0}
                            }
                            mock_reddit.return_value = {'average_sentiment': 0.2, 'posts_analyzed': 0}
                            mock_events.return_value = {'events_detected': []}
                            
                            # Run full analysis
                            result = analyzer.analyze_bank_sentiment('CBA.AX')
                            
                            # Verify complete result structure
                            required_keys = [
                                'symbol', 'timestamp', 'news_count', 'sentiment_scores',
                                'reddit_sentiment', 'significant_events', 'overall_sentiment',
                                'confidence', 'recent_headlines'
                            ]
                            
                            for key in required_keys:
                                self.assertIn(key, result, f"Missing key: {key}")
                            
                            self.assertEqual(result['symbol'], 'CBA.AX')
                            self.assertIsInstance(result['overall_sentiment'], (int, float))
                            self.assertIsInstance(result['confidence'], (int, float))


def create_test_suite():
    """Create a comprehensive test suite"""
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestNewsSentimentAnalyzer,
        TestDatabaseOperations,
        TestNewsCollectorIntegration,
        TestMLModelIntegration,
        TestSystemIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    return test_suite


if __name__ == '__main__':
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    suite = create_test_suite()
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('Error:')[-1].strip()}")
    
    # Exit with error code if tests failed
    sys.exit(0 if result.wasSuccessful() else 1)
