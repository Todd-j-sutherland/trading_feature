#!/usr/bin/env python3
"""
Test Utilities and Helpers
Common functions and mocks for testing
"""

import os
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
import random

class TestDataGenerator:
    """Generate test data for various components"""
    
    @staticmethod
    def generate_sentiment_data(symbol="CBA.AX", sentiment=None, confidence=None):
        """Generate mock sentiment data"""
        return {
            'symbol': symbol,
            'overall_sentiment': sentiment or random.uniform(-1.0, 1.0),
            'confidence': confidence or random.uniform(0.0, 1.0),
            'news_count': random.randint(1, 30),
            'reddit_sentiment': random.uniform(-1.0, 1.0),
            'event_score': random.uniform(-1.0, 1.0),
            'sentiment_confidence_interaction': random.uniform(-1.0, 1.0),
            'news_volume_category': random.randint(0, 1),
            'hour': random.randint(0, 23),
            'day_of_week': random.randint(0, 6),
            'is_market_hours': random.randint(0, 1),
            'timestamp': datetime.now().isoformat(),
            'news_articles': [f"Test article {i}" for i in range(random.randint(1, 5))]
        }
    
    @staticmethod
    def generate_trading_data(symbol="CBA.AX", signal="HOLD"):
        """Generate mock trading data"""
        return {
            'symbol': symbol,
            'signal': signal,
            'sentiment_score': random.uniform(-1.0, 1.0),
            'confidence': random.uniform(0.0, 1.0),
            'current_price': random.uniform(90.0, 120.0),
            'entry_price': random.uniform(90.0, 120.0),
            'timestamp': datetime.now().isoformat(),
            'trade_id': f"trade_{random.randint(1000, 9999)}",
            'recommendation': signal,
            'strategy': 'moderate'
        }
    
    @staticmethod
    def generate_ml_training_data(num_samples=100):
        """Generate mock ML training data"""
        features = []
        labels = []
        
        for _ in range(num_samples):
            feature_vector = [
                random.uniform(-1.0, 1.0),    # sentiment_score
                random.uniform(0.0, 1.0),     # confidence
                random.randint(1, 30),        # news_count
                random.uniform(-1.0, 1.0),    # reddit_sentiment
                random.uniform(-1.0, 1.0),    # event_score
                random.uniform(-1.0, 1.0),    # interaction
                random.randint(0, 1),         # volume_category
                random.randint(0, 23),        # hour
                random.randint(0, 6),         # day_of_week
                random.randint(0, 1)          # is_market_hours
            ]
            
            features.append(feature_vector)
            labels.append(random.randint(0, 1))  # Binary classification
        
        return features, labels
    
    @staticmethod
    def generate_performance_data():
        """Generate mock performance data"""
        return {
            'total_trades': random.randint(10, 100),
            'winning_trades': random.randint(5, 60),
            'total_return': random.uniform(-0.1, 0.3),
            'max_drawdown': random.uniform(-0.1, 0.0),
            'sharpe_ratio': random.uniform(0.0, 2.0),
            'win_rate': random.uniform(0.4, 0.8),
            'average_return': random.uniform(-0.02, 0.05),
            'volatility': random.uniform(0.1, 0.3)
        }

class MockComponents:
    """Mock versions of system components"""
    
    @staticmethod
    def mock_ml_pipeline():
        """Create mock ML pipeline"""
        mock = Mock()
        mock.prepare_training_dataset.return_value = (
            TestDataGenerator.generate_ml_training_data(87)
        )
        mock.train_models.return_value = {
            'best_model': 'logistic_regression',
            'model_scores': {'logistic_regression': {'avg_cv_score': 0.606}}
        }
        mock.collect_training_data.return_value = random.randint(1, 1000)
        return mock
    
    @staticmethod
    def mock_sentiment_analyzer():
        """Create mock sentiment analyzer"""
        mock = Mock()
        mock.analyze_bank_sentiment.return_value = TestDataGenerator.generate_sentiment_data()
        mock._get_ml_prediction.return_value = {
            'prediction': 'HOLD',
            'confidence': 0.75,
            'ml_score': 0.1
        }
        return mock
    
    @staticmethod
    def mock_trading_analyzer():
        """Create mock trading analyzer"""
        mock = Mock()
        mock.analyze_symbol.return_value = TestDataGenerator.generate_trading_data()
        mock.analyze_and_track.return_value = TestDataGenerator.generate_trading_data()
        mock.close_trade.return_value = True
        return mock
    
    @staticmethod
    def mock_data_feed():
        """Create mock data feed"""
        mock = Mock()
        mock.get_current_data.return_value = {
            'price': random.uniform(90.0, 120.0),
            'volume': random.randint(1000000, 5000000),
            'timestamp': datetime.now().isoformat()
        }
        return mock

class TestFileManager:
    """Manage test files and directories"""
    
    def __init__(self):
        self.temp_dirs = []
        self.temp_files = []
    
    def create_temp_dir(self):
        """Create temporary directory"""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def create_temp_file(self, content="", suffix=".json"):
        """Create temporary file"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False)
        temp_file.write(content)
        temp_file.close()
        self.temp_files.append(temp_file.name)
        return temp_file.name
    
    def create_mock_data_structure(self, base_dir):
        """Create mock data directory structure"""
        subdirs = [
            'data/ml_models/models',
            'data/sentiment_history',
            'reports',
            'logs'
        ]
        
        for subdir in subdirs:
            full_path = os.path.join(base_dir, subdir)
            os.makedirs(full_path, exist_ok=True)
        
        # Create mock files
        mock_files = {
            'data/ml_models/models/current_model.pkl': b'mock_model_data',
            'data/ml_models/models/current_metadata.json': json.dumps({
                'model_type': 'logistic_regression',
                'cv_score': 0.606,
                'feature_columns': ['sentiment_score', 'confidence']
            }),
            'data/sentiment_history/CBA.AX_history.json': json.dumps([
                TestDataGenerator.generate_sentiment_data("CBA.AX") for _ in range(5)
            ])
        }
        
        for file_path, content in mock_files.items():
            full_path = os.path.join(base_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            mode = 'wb' if isinstance(content, bytes) else 'w'
            with open(full_path, mode) as f:
                f.write(content)
    
    def cleanup(self):
        """Clean up temporary files and directories"""
        for temp_file in self.temp_files:
            try:
                os.unlink(temp_file)
            except OSError:
                pass
        
        for temp_dir in self.temp_dirs:
            try:
                shutil.rmtree(temp_dir)
            except OSError:
                pass
        
        self.temp_files.clear()
        self.temp_dirs.clear()

class TestAssertions:
    """Custom test assertions"""
    
    @staticmethod
    def assert_sentiment_data_valid(test_case, sentiment_data):
        """Assert sentiment data is valid"""
        required_fields = ['overall_sentiment', 'confidence', 'news_count', 'timestamp']
        for field in required_fields:
            test_case.assertIn(field, sentiment_data)
        
        test_case.assertGreaterEqual(sentiment_data['overall_sentiment'], -1.0)
        test_case.assertLessEqual(sentiment_data['overall_sentiment'], 1.0)
        test_case.assertGreaterEqual(sentiment_data['confidence'], 0.0)
        test_case.assertLessEqual(sentiment_data['confidence'], 1.0)
        test_case.assertGreaterEqual(sentiment_data['news_count'], 0)
    
    @staticmethod
    def assert_trading_signal_valid(test_case, trading_data):
        """Assert trading signal is valid"""
        test_case.assertIn('signal', trading_data)
        test_case.assertIn(trading_data['signal'], ['BUY', 'SELL', 'HOLD'])
        
        if 'confidence' in trading_data:
            test_case.assertGreaterEqual(trading_data['confidence'], 0.0)
            test_case.assertLessEqual(trading_data['confidence'], 1.0)
    
    @staticmethod
    def assert_ml_data_valid(test_case, features, labels):
        """Assert ML training data is valid"""
        test_case.assertEqual(len(features), len(labels))
        test_case.assertGreater(len(features), 0)
        
        if len(features) > 0:
            test_case.assertIsInstance(features[0], list)
            test_case.assertGreater(len(features[0]), 5)  # At least 5 features
    
    @staticmethod
    def assert_performance_metrics_valid(test_case, performance_data):
        """Assert performance metrics are valid"""
        required_metrics = ['total_trades', 'win_rate', 'total_return']
        for metric in required_metrics:
            test_case.assertIn(metric, performance_data)
        
        test_case.assertGreaterEqual(performance_data['total_trades'], 0)
        test_case.assertGreaterEqual(performance_data['win_rate'], 0.0)
        test_case.assertLessEqual(performance_data['win_rate'], 1.0)

# Global test utilities instance
test_file_manager = TestFileManager()

def cleanup_test_files():
    """Global cleanup function"""
    test_file_manager.cleanup()
