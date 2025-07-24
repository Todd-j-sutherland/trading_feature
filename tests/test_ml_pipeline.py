#!/usr/bin/env python3
"""
Tests for ML training pipeline
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
import shutil
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.ml.training.pipeline import MLTrainingPipeline

class TestMLPipeline(unittest.TestCase):
    
    def setUp(self):
        # Create temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        self.pipeline = MLTrainingPipeline(data_dir=self.test_dir)
    
    def tearDown(self):
        # Clean up
        shutil.rmtree(self.test_dir)
    
    def test_collect_training_data(self):
        """Test collecting sentiment data for training"""
        sentiment_data = {
            'symbol': 'CBA.AX',
            'timestamp': datetime.now().isoformat(),
            'overall_sentiment': 0.5,
            'confidence': 0.8,
            'news_count': 10,
            'reddit_sentiment': {'average_sentiment': 0.3},
            'sentiment_components': {'events': 0.2}
        }
        
        feature_id = self.pipeline.collect_training_data(sentiment_data, 'CBA.AX')
        self.assertIsNotNone(feature_id)
        self.assertGreater(feature_id, 0)
    
    def test_record_trading_outcome(self):
        """Test recording trading outcomes"""
        # First create a feature entry
        sentiment_data = {
            'symbol': 'CBA.AX',
            'timestamp': datetime.now().isoformat(),
            'overall_sentiment': 0.5,
            'confidence': 0.8,
            'news_count': 10,
            'reddit_sentiment': {'average_sentiment': 0.3},
            'sentiment_components': {'events': 0.2}
        }
        
        feature_id = self.pipeline.collect_training_data(sentiment_data, 'CBA.AX')
        
        # Record outcome
        outcome_data = {
            'symbol': 'CBA.AX',
            'signal_timestamp': datetime.now().isoformat(),
            'signal_type': 'BUY',
            'entry_price': 100.0,
            'exit_price': 105.0,
            'exit_timestamp': (datetime.now() + timedelta(days=5)).isoformat()
        }
        
        self.pipeline.record_trading_outcome(feature_id, outcome_data)
        
        # Verify data was stored
        X, y = self.pipeline.prepare_training_dataset(min_samples=1)
        self.assertIsNotNone(X)
        self.assertIsNotNone(y)
        self.assertEqual(len(X), 1)
        self.assertEqual(y.iloc[0], 1)  # Should be profitable
    
    def test_model_training(self):
        """Test model training with synthetic data"""
        # Create synthetic training data
        n_samples = 200
        
        # Generate features
        np.random.seed(42)
        X = pd.DataFrame({
            'sentiment_score': np.random.uniform(-1, 1, n_samples),
            'confidence': np.random.uniform(0.3, 1, n_samples),
            'news_count': np.random.randint(1, 20, n_samples),
            'reddit_sentiment': np.random.uniform(-1, 1, n_samples),
            'event_score': np.random.uniform(-0.5, 0.5, n_samples),
            'sentiment_confidence_interaction': np.random.uniform(-1, 1, n_samples),
            'news_volume_category': np.random.randint(0, 4, n_samples),
            'hour': np.random.randint(0, 24, n_samples),
            'day_of_week': np.random.randint(0, 7, n_samples),
            'is_market_hours': np.random.randint(0, 2, n_samples)
        })
        
        # Generate labels (with some correlation to features)
        y = pd.Series((X['sentiment_score'] + X['confidence'] + 
                      np.random.normal(0, 0.5, n_samples)) > 0.5).astype(int)
        
        # Train models
        results = self.pipeline.train_models(X, y)
        
        self.assertIn('best_model', results)
        self.assertIn('model_scores', results)
        self.assertGreater(len(results['model_scores']), 0)

if __name__ == '__main__':
    unittest.main()
