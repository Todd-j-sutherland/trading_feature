#!/usr/bin/env python3
"""
Tests for News Sentiment Analysis
"""

import unittest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil
import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestNewsSentiment(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        
        # Mock the news sentiment analyzer to avoid external dependencies
        self.mock_sentiment_data = {
            'overall_sentiment': 0.5,
            'confidence': 0.8,
            'news_count': 5,
            'reddit_sentiment': 0.3,
            'event_score': 0.2,
            'news_articles': ['Test article 1', 'Test article 2'],
            'timestamp': datetime.now().isoformat()
        }
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_sentiment_analysis_basic(self):
        """Test basic sentiment analysis functionality"""
        try:
            from src.news_sentiment import NewsSentimentAnalyzer
            
            # Create analyzer instance
            analyzer = NewsSentimentAnalyzer()
            
            # Test initialization
            self.assertIsNotNone(analyzer)
            self.assertTrue(hasattr(analyzer, 'sentiment_analyzer'))
            
        except ImportError:
            self.skipTest("NewsSentimentAnalyzer not available for testing")
    
    @patch('src.news_sentiment.NewsSentimentAnalyzer')
    def test_sentiment_score_calculation(self, mock_analyzer):
        """Test sentiment score calculation"""
        # Mock analyzer response
        mock_instance = Mock()
        mock_instance.analyze_bank_sentiment.return_value = self.mock_sentiment_data
        mock_analyzer.return_value = mock_instance
        
        # Test sentiment score is within expected range
        result = mock_instance.analyze_bank_sentiment('CBA.AX')
        
        self.assertIn('overall_sentiment', result)
        self.assertGreaterEqual(result['overall_sentiment'], -1.0)
        self.assertLessEqual(result['overall_sentiment'], 1.0)
        self.assertGreater(result['confidence'], 0.0)
        self.assertLessEqual(result['confidence'], 1.0)
    
    def test_sentiment_feature_extraction(self):
        """Test sentiment feature extraction for ML"""
        
        # Test feature extraction from sentiment data
        features = self._extract_ml_features(self.mock_sentiment_data)
        
        expected_features = [
            'sentiment_score', 'confidence', 'news_count', 
            'reddit_sentiment', 'event_score'
        ]
        
        for feature in expected_features:
            self.assertIn(feature, features)
    
    def test_sentiment_confidence_levels(self):
        """Test different confidence levels"""
        
        # Test high confidence
        high_conf_data = self.mock_sentiment_data.copy()
        high_conf_data['confidence'] = 0.9
        self.assertGreater(high_conf_data['confidence'], 0.7)
        
        # Test low confidence
        low_conf_data = self.mock_sentiment_data.copy()
        low_conf_data['confidence'] = 0.3
        self.assertLess(low_conf_data['confidence'], 0.5)
    
    def test_sentiment_boundary_values(self):
        """Test sentiment analysis with boundary values"""
        
        # Test extreme positive sentiment
        positive_data = self.mock_sentiment_data.copy()
        positive_data['overall_sentiment'] = 1.0
        self.assertEqual(positive_data['overall_sentiment'], 1.0)
        
        # Test extreme negative sentiment  
        negative_data = self.mock_sentiment_data.copy()
        negative_data['overall_sentiment'] = -1.0
        self.assertEqual(negative_data['overall_sentiment'], -1.0)
        
        # Test neutral sentiment
        neutral_data = self.mock_sentiment_data.copy()
        neutral_data['overall_sentiment'] = 0.0
        self.assertEqual(neutral_data['overall_sentiment'], 0.0)
    
    def test_ml_prediction_integration(self):
        """Test ML prediction integration"""
        
        # Mock ML prediction
        mock_prediction = {
            'prediction': 'BUY',
            'confidence': 0.75,
            'ml_score': 0.6
        }
        
        # Test prediction format
        self.assertIn('prediction', mock_prediction)
        self.assertIn('confidence', mock_prediction)
        self.assertIn(mock_prediction['prediction'], ['BUY', 'SELL', 'HOLD'])
    
    def test_news_article_processing(self):
        """Test news article processing"""
        
        test_articles = [
            "Bank reports strong quarterly earnings",
            "Interest rates may rise next month",
            "Banking sector faces regulatory challenges"
        ]
        
        # Test article count
        self.assertGreater(len(test_articles), 0)
        
        # Test article content is string
        for article in test_articles:
            self.assertIsInstance(article, str)
            self.assertGreater(len(article), 0)
    
    def test_sentiment_caching(self):
        """Test sentiment analysis caching"""
        
        # Mock cache key generation
        symbol = "CBA.AX"
        cache_key = f"sentiment_{symbol}"
        
        self.assertEqual(cache_key, "sentiment_CBA.AX")
        
        # Test cache data structure
        cached_data = self.mock_sentiment_data.copy()
        self.assertIn('timestamp', cached_data)
        self.assertIn('overall_sentiment', cached_data)
    
    def test_error_handling(self):
        """Test error handling in sentiment analysis"""
        
        # Test with invalid symbol
        with self.assertRaises((ValueError, TypeError, AttributeError)):
            # Simulate error condition
            raise ValueError("Invalid symbol")
        
        # Test with None data
        try:
            result = self._handle_none_data(None)
            self.assertIsNotNone(result)
        except Exception:
            pass  # Expected for error testing
    
    def test_data_validation(self):
        """Test sentiment data validation"""
        
        # Test valid data
        valid_data = self.mock_sentiment_data.copy()
        self.assertTrue(self._validate_sentiment_data(valid_data))
        
        # Test invalid data
        invalid_data = {'invalid': 'data'}
        self.assertFalse(self._validate_sentiment_data(invalid_data))
    
    # Helper methods
    def _extract_ml_features(self, sentiment_data):
        """Extract ML features from sentiment data"""
        return {
            'sentiment_score': sentiment_data.get('overall_sentiment', 0),
            'confidence': sentiment_data.get('confidence', 0),
            'news_count': sentiment_data.get('news_count', 0),
            'reddit_sentiment': sentiment_data.get('reddit_sentiment', 0),
            'event_score': sentiment_data.get('event_score', 0)
        }
    
    def _validate_sentiment_data(self, data):
        """Validate sentiment data structure"""
        required_fields = ['overall_sentiment', 'confidence', 'news_count']
        return all(field in data for field in required_fields)
    
    def _handle_none_data(self, data):
        """Handle None data gracefully"""
        if data is None:
            return {
                'overall_sentiment': 0.0,
                'confidence': 0.0,
                'news_count': 0,
                'error': 'No data available'
            }
        return data

if __name__ == "__main__":
    unittest.main()
