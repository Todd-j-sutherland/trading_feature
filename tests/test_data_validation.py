#!/usr/bin/env python3
"""
Data Validation Tests
Tests for validating data integrity in database tables and JSON files
"""

import os
import sys
import json
import sqlite3
import unittest
from pathlib import Path
from datetime import datetime, timedelta
import tempfile

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestDatabaseDataValidation(unittest.TestCase):
    """Test database table data integrity"""
    
    def setUp(self):
        """Set up test database"""
        self.test_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.test_db.name
        self.test_db.close()
        
        # Create test database with sample data
        self.conn = sqlite3.connect(self.db_path)
        self.create_test_tables()
        self.populate_test_data()
    
    def tearDown(self):
        """Clean up test database"""
        if hasattr(self, 'conn'):
            self.conn.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def create_test_tables(self):
        """Create test database tables"""
        cursor = self.conn.cursor()
        
        # Sentiment analysis table
        cursor.execute('''
            CREATE TABLE sentiment_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                sentiment_score REAL NOT NULL,
                confidence REAL NOT NULL,
                timestamp TEXT NOT NULL,
                news_source TEXT,
                headline TEXT
            )
        ''')
        
        # Technical analysis table
        cursor.execute('''
            CREATE TABLE technical_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                technical_score REAL NOT NULL,
                rsi REAL,
                macd REAL,
                bollinger_position REAL,
                timestamp TEXT NOT NULL
            )
        ''')
        
        # Trading signals table
        cursor.execute('''
            CREATE TABLE trading_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                strength REAL NOT NULL,
                timestamp TEXT NOT NULL,
                reasoning TEXT
            )
        ''')
        
        # ML predictions table
        cursor.execute('''
            CREATE TABLE ml_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                prediction REAL NOT NULL,
                confidence REAL NOT NULL,
                model_version TEXT,
                timestamp TEXT NOT NULL
            )
        ''')
        
        self.conn.commit()
    
    def populate_test_data(self):
        """Populate tables with test data"""
        cursor = self.conn.cursor()
        
        # Sample sentiment data
        sentiment_data = [
            ('CBA.AX', 0.75, 0.85, '2025-01-20 10:00:00', 'Reuters', 'Bank reports strong earnings'),
            ('ANZ.AX', -0.25, 0.70, '2025-01-20 11:00:00', 'Bloomberg', 'Regulatory concerns raised'),
            ('WBC.AX', 0.45, 0.60, '2025-01-20 12:00:00', 'AFR', 'Mixed quarterly results'),
            ('NAB.AX', 0.0, 0.0, '2025-01-20 13:00:00', 'Test', 'Invalid zero scores'),  # Test invalid data
        ]
        
        cursor.executemany('''
            INSERT INTO sentiment_analysis (symbol, sentiment_score, confidence, timestamp, news_source, headline)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', sentiment_data)
        
        # Sample technical data
        technical_data = [
            ('CBA.AX', 0.68, 65.5, 0.25, 0.75, '2025-01-20 10:00:00'),
            ('ANZ.AX', -0.45, 35.2, -0.15, -0.25, '2025-01-20 11:00:00'),
            ('WBC.AX', 0.12, 52.8, 0.05, 0.15, '2025-01-20 12:00:00'),
            ('NAB.AX', 0.0, 50.0, 0.0, 0.0, '2025-01-20 13:00:00'),  # Test zero scores
        ]
        
        cursor.executemany('''
            INSERT INTO technical_analysis (symbol, technical_score, rsi, macd, bollinger_position, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', technical_data)
        
        # Sample trading signals
        signal_data = [
            ('CBA.AX', 'BUY', 0.85, '2025-01-20 10:00:00', 'Strong sentiment and technical indicators'),
            ('ANZ.AX', 'SELL', 0.70, '2025-01-20 11:00:00', 'Negative sentiment outweighs technical'),
            ('WBC.AX', 'HOLD', 0.45, '2025-01-20 12:00:00', 'Mixed signals suggest caution'),
        ]
        
        cursor.executemany('''
            INSERT INTO trading_signals (symbol, signal_type, strength, timestamp, reasoning)
            VALUES (?, ?, ?, ?, ?)
        ''', signal_data)
        
        # Sample ML predictions
        ml_data = [
            ('CBA.AX', 0.72, 0.88, 'v2.1.0', '2025-01-20 10:00:00'),
            ('ANZ.AX', -0.38, 0.75, 'v2.1.0', '2025-01-20 11:00:00'),
            ('WBC.AX', 0.15, 0.62, 'v2.1.0', '2025-01-20 12:00:00'),
        ]
        
        cursor.executemany('''
            INSERT INTO ml_predictions (symbol, prediction, confidence, model_version, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', ml_data)
        
        self.conn.commit()
    
    def test_sentiment_data_integrity(self):
        """Test sentiment analysis data integrity"""
        cursor = self.conn.cursor()
        
        # Test for zero sentiment scores (should be flagged)
        cursor.execute('''
            SELECT COUNT(*) FROM sentiment_analysis 
            WHERE sentiment_score = 0.0 AND confidence = 0.0
        ''')
        zero_scores = cursor.fetchone()[0]
        self.assertGreater(zero_scores, 0, "Should detect zero sentiment scores for testing")
        
        # Test sentiment score range
        cursor.execute('SELECT sentiment_score FROM sentiment_analysis')
        scores = [row[0] for row in cursor.fetchall()]
        for score in scores:
            if score != 0.0:  # Allow test zero scores
                self.assertTrue(-1.0 <= score <= 1.0, f"Sentiment score {score} out of valid range [-1, 1]")
        
        # Test confidence range
        cursor.execute('SELECT confidence FROM sentiment_analysis')
        confidences = [row[0] for row in cursor.fetchall()]
        for conf in confidences:
            if conf != 0.0:  # Allow test zero confidence
                self.assertTrue(0.0 <= conf <= 1.0, f"Confidence {conf} out of valid range [0, 1]")
        
        # Test required fields
        cursor.execute('SELECT symbol, timestamp FROM sentiment_analysis')
        records = cursor.fetchall()
        for symbol, timestamp in records:
            self.assertIsNotNone(symbol, "Symbol should not be None")
            self.assertIsNotNone(timestamp, "Timestamp should not be None")
            self.assertTrue(len(symbol) > 0, "Symbol should not be empty")
    
    def test_technical_data_integrity(self):
        """Test technical analysis data integrity"""
        cursor = self.conn.cursor()
        
        # Test technical score range
        cursor.execute('SELECT technical_score FROM technical_analysis')
        scores = [row[0] for row in cursor.fetchall()]
        for score in scores:
            if score != 0.0:  # Allow test zero scores
                self.assertTrue(-1.0 <= score <= 1.0, f"Technical score {score} out of valid range [-1, 1]")
        
        # Test RSI range
        cursor.execute('SELECT rsi FROM technical_analysis WHERE rsi IS NOT NULL')
        rsi_values = [row[0] for row in cursor.fetchall()]
        for rsi in rsi_values:
            self.assertTrue(0.0 <= rsi <= 100.0, f"RSI {rsi} out of valid range [0, 100]")
        
        # Test Bollinger Band position range
        cursor.execute('SELECT bollinger_position FROM technical_analysis WHERE bollinger_position IS NOT NULL')
        bb_values = [row[0] for row in cursor.fetchall()]
        for bb in bb_values:
            self.assertTrue(-1.0 <= bb <= 1.0, f"Bollinger position {bb} out of valid range [-1, 1]")
    
    def test_trading_signals_integrity(self):
        """Test trading signals data integrity"""
        cursor = self.conn.cursor()
        
        # Test valid signal types
        cursor.execute('SELECT DISTINCT signal_type FROM trading_signals')
        signal_types = [row[0] for row in cursor.fetchall()]
        valid_types = {'BUY', 'SELL', 'HOLD'}
        for signal_type in signal_types:
            self.assertIn(signal_type, valid_types, f"Invalid signal type: {signal_type}")
        
        # Test strength range
        cursor.execute('SELECT strength FROM trading_signals')
        strengths = [row[0] for row in cursor.fetchall()]
        for strength in strengths:
            self.assertTrue(0.0 <= strength <= 1.0, f"Signal strength {strength} out of valid range [0, 1]")
        
        # Test that all signals have reasoning
        cursor.execute('SELECT reasoning FROM trading_signals')
        reasonings = [row[0] for row in cursor.fetchall()]
        for reasoning in reasonings:
            self.assertIsNotNone(reasoning, "Signal reasoning should not be None")
            self.assertTrue(len(reasoning) > 0, "Signal reasoning should not be empty")
    
    def test_ml_predictions_integrity(self):
        """Test ML predictions data integrity"""
        cursor = self.conn.cursor()
        
        # Test prediction range
        cursor.execute('SELECT prediction FROM ml_predictions')
        predictions = [row[0] for row in cursor.fetchall()]
        for prediction in predictions:
            self.assertTrue(-1.0 <= prediction <= 1.0, f"ML prediction {prediction} out of valid range [-1, 1]")
        
        # Test confidence range
        cursor.execute('SELECT confidence FROM ml_predictions')
        confidences = [row[0] for row in cursor.fetchall()]
        for conf in confidences:
            self.assertTrue(0.0 <= conf <= 1.0, f"ML confidence {conf} out of valid range [0, 1]")
        
        # Test model version format
        cursor.execute('SELECT model_version FROM ml_predictions WHERE model_version IS NOT NULL')
        versions = [row[0] for row in cursor.fetchall()]
        for version in versions:
            self.assertRegex(version, r'^v\d+\.\d+\.\d+$', f"Invalid model version format: {version}")
    
    def test_data_consistency(self):
        """Test data consistency across tables"""
        cursor = self.conn.cursor()
        
        # Get symbols from each table
        cursor.execute('SELECT DISTINCT symbol FROM sentiment_analysis')
        sentiment_symbols = set(row[0] for row in cursor.fetchall())
        
        cursor.execute('SELECT DISTINCT symbol FROM technical_analysis')
        technical_symbols = set(row[0] for row in cursor.fetchall())
        
        cursor.execute('SELECT DISTINCT symbol FROM trading_signals')
        signal_symbols = set(row[0] for row in cursor.fetchall())
        
        # Test that signals exist for symbols with both sentiment and technical data
        common_symbols = sentiment_symbols.intersection(technical_symbols)
        missing_signals = common_symbols - signal_symbols
        
        # Allow for some missing signals in test data, but flag if completely absent
        if missing_signals and len(missing_signals) == len(common_symbols):
            self.fail(f"No trading signals found for any symbols with both sentiment and technical data")
    
    def test_timestamp_validity(self):
        """Test timestamp format and validity"""
        cursor = self.conn.cursor()
        
        tables = ['sentiment_analysis', 'technical_analysis', 'trading_signals', 'ml_predictions']
        
        for table in tables:
            cursor.execute(f'SELECT timestamp FROM {table}')
            timestamps = [row[0] for row in cursor.fetchall()]
            
            for ts in timestamps:
                # Test timestamp format (ISO format or similar)
                try:
                    # Try to parse timestamp
                    datetime.fromisoformat(ts.replace(' ', 'T'))
                except ValueError:
                    self.fail(f"Invalid timestamp format in {table}: {ts}")


class TestJSONDataValidation(unittest.TestCase):
    """Test JSON file data integrity"""
    
    def setUp(self):
        """Set up test JSON files"""
        self.test_dir = tempfile.mkdtemp()
        self.create_test_json_files()
    
    def tearDown(self):
        """Clean up test files"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_test_json_files(self):
        """Create test JSON files with sample data"""
        
        # Sentiment history JSON
        sentiment_history = {
            "CBA.AX": [
                {
                    "timestamp": "2025-01-20T10:00:00",
                    "sentiment": 0.75,
                    "confidence": 0.85,
                    "source": "news_analysis"
                },
                {
                    "timestamp": "2025-01-20T11:00:00",
                    "sentiment": 0.0,  # Test zero value
                    "confidence": 0.0,  # Test zero value
                    "source": "news_analysis"
                }
            ],
            "ANZ.AX": [
                {
                    "timestamp": "2025-01-20T10:00:00",
                    "sentiment": -0.25,
                    "confidence": 0.70,
                    "source": "news_analysis"
                }
            ]
        }
        
        with open(os.path.join(self.test_dir, 'sentiment_history.json'), 'w') as f:
            json.dump(sentiment_history, f, indent=2)
        
        # ML performance data
        ml_performance = {
            "model_metrics": {
                "accuracy": 0.85,
                "precision": 0.82,
                "recall": 0.87,
                "f1_score": 0.84
            },
            "training_history": [
                {
                    "epoch": 1,
                    "loss": 0.45,
                    "accuracy": 0.78,
                    "val_loss": 0.52,
                    "val_accuracy": 0.76
                },
                {
                    "epoch": 2,
                    "loss": 0.38,
                    "accuracy": 0.82,
                    "val_loss": 0.48,
                    "val_accuracy": 0.80
                }
            ],
            "feature_importance": {
                "sentiment_score": 0.35,
                "technical_indicators": 0.28,
                "volume": 0.20,
                "price_momentum": 0.17
            }
        }
        
        with open(os.path.join(self.test_dir, 'ml_performance.json'), 'w') as f:
            json.dump(ml_performance, f, indent=2)
        
        # Trading results JSON
        trading_results = {
            "portfolio_value": 150000.0,
            "total_return": 0.15,
            "trades": [
                {
                    "symbol": "CBA.AX",
                    "action": "BUY",
                    "quantity": 100,
                    "price": 85.50,
                    "timestamp": "2025-01-20T10:00:00",
                    "reasoning": "Strong sentiment and technical signals"
                },
                {
                    "symbol": "ANZ.AX",
                    "action": "SELL",
                    "quantity": 50,
                    "price": 22.75,
                    "timestamp": "2025-01-20T11:00:00",
                    "reasoning": "Negative sentiment override"
                }
            ],
            "performance_metrics": {
                "sharpe_ratio": 1.25,
                "max_drawdown": -0.08,
                "win_rate": 0.65,
                "avg_return_per_trade": 0.025
            }
        }
        
        with open(os.path.join(self.test_dir, 'trading_results.json'), 'w') as f:
            json.dump(trading_results, f, indent=2)
        
        # Configuration JSON
        config_data = {
            "trading_parameters": {
                "sentiment_threshold": 0.6,
                "technical_threshold": 0.5,
                "confidence_threshold": 0.7,
                "max_position_size": 0.1
            },
            "data_sources": {
                "news_apis": ["reuters", "bloomberg", "afr"],
                "technical_data": "alpaca",
                "update_frequency": 300
            },
            "risk_management": {
                "stop_loss": -0.05,
                "take_profit": 0.10,
                "max_daily_loss": -0.02
            }
        }
        
        with open(os.path.join(self.test_dir, 'config.json'), 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def test_json_file_validity(self):
        """Test that JSON files are valid and parseable"""
        json_files = [
            'sentiment_history.json',
            'ml_performance.json',
            'trading_results.json',
            'config.json'
        ]
        
        for json_file in json_files:
            file_path = os.path.join(self.test_dir, json_file)
            with self.subTest(json_file=json_file):
                self.assertTrue(os.path.exists(file_path), f"JSON file {json_file} should exist")
                
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    self.assertIsInstance(data, (dict, list), f"JSON file {json_file} should contain valid JSON")
                except json.JSONDecodeError as e:
                    self.fail(f"JSON file {json_file} contains invalid JSON: {e}")
    
    def test_sentiment_history_structure(self):
        """Test sentiment history JSON structure and data"""
        file_path = os.path.join(self.test_dir, 'sentiment_history.json')
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        self.assertIsInstance(data, dict, "Sentiment history should be a dictionary")
        
        for symbol, history in data.items():
            with self.subTest(symbol=symbol):
                self.assertIsInstance(history, list, f"History for {symbol} should be a list")
                
                for entry in history:
                    self.assertIn('timestamp', entry, "Entry should have timestamp")
                    self.assertIn('sentiment', entry, "Entry should have sentiment")
                    self.assertIn('confidence', entry, "Entry should have confidence")
                    
                    # Test data ranges (allowing test zero values)
                    sentiment = entry['sentiment']
                    confidence = entry['confidence']
                    
                    if sentiment != 0.0:  # Allow test zero values
                        self.assertTrue(-1.0 <= sentiment <= 1.0, f"Sentiment {sentiment} out of range")
                    
                    if confidence != 0.0:  # Allow test zero values
                        self.assertTrue(0.0 <= confidence <= 1.0, f"Confidence {confidence} out of range")
    
    def test_ml_performance_structure(self):
        """Test ML performance JSON structure and data"""
        file_path = os.path.join(self.test_dir, 'ml_performance.json')
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Test required sections
        required_sections = ['model_metrics', 'training_history', 'feature_importance']
        for section in required_sections:
            self.assertIn(section, data, f"ML performance should have {section} section")
        
        # Test model metrics
        metrics = data['model_metrics']
        metric_names = ['accuracy', 'precision', 'recall', 'f1_score']
        for metric in metric_names:
            self.assertIn(metric, metrics, f"Should have {metric} in model_metrics")
            value = metrics[metric]
            self.assertTrue(0.0 <= value <= 1.0, f"{metric} {value} should be between 0 and 1")
        
        # Test training history
        history = data['training_history']
        self.assertIsInstance(history, list, "Training history should be a list")
        for epoch_data in history:
            self.assertIn('epoch', epoch_data, "Epoch data should have epoch number")
            self.assertIn('loss', epoch_data, "Epoch data should have loss")
            self.assertIn('accuracy', epoch_data, "Epoch data should have accuracy")
    
    def test_trading_results_structure(self):
        """Test trading results JSON structure and data"""
        file_path = os.path.join(self.test_dir, 'trading_results.json')
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Test required fields
        required_fields = ['portfolio_value', 'total_return', 'trades', 'performance_metrics']
        for field in required_fields:
            self.assertIn(field, data, f"Trading results should have {field}")
        
        # Test portfolio value is positive
        self.assertGreater(data['portfolio_value'], 0, "Portfolio value should be positive")
        
        # Test trades structure
        trades = data['trades']
        self.assertIsInstance(trades, list, "Trades should be a list")
        
        for trade in trades:
            required_trade_fields = ['symbol', 'action', 'quantity', 'price', 'timestamp']
            for field in required_trade_fields:
                self.assertIn(field, trade, f"Trade should have {field}")
            
            # Test trade action validity
            self.assertIn(trade['action'], ['BUY', 'SELL', 'HOLD'], f"Invalid trade action: {trade['action']}")
            
            # Test positive quantities and prices
            self.assertGreater(trade['quantity'], 0, "Trade quantity should be positive")
            self.assertGreater(trade['price'], 0, "Trade price should be positive")
    
    def test_config_structure(self):
        """Test configuration JSON structure and data"""
        file_path = os.path.join(self.test_dir, 'config.json')
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Test required sections
        required_sections = ['trading_parameters', 'data_sources', 'risk_management']
        for section in required_sections:
            self.assertIn(section, data, f"Config should have {section} section")
        
        # Test trading parameters
        params = data['trading_parameters']
        threshold_params = ['sentiment_threshold', 'technical_threshold', 'confidence_threshold']
        for param in threshold_params:
            self.assertIn(param, params, f"Should have {param} in trading_parameters")
            value = params[param]
            self.assertTrue(0.0 <= value <= 1.0, f"{param} {value} should be between 0 and 1")
        
        # Test risk management parameters
        risk = data['risk_management']
        self.assertIn('stop_loss', risk, "Should have stop_loss in risk_management")
        self.assertIn('take_profit', risk, "Should have take_profit in risk_management")
        
        # Stop loss should be negative, take profit positive
        self.assertLess(risk['stop_loss'], 0, "Stop loss should be negative")
        self.assertGreater(risk['take_profit'], 0, "Take profit should be positive")
    
    def test_data_freshness(self):
        """Test that JSON data timestamps are reasonable"""
        file_path = os.path.join(self.test_dir, 'sentiment_history.json')
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        now = datetime.now()
        max_age_days = 30  # Data shouldn't be older than 30 days for active trading
        
        for symbol, history in data.items():
            for entry in history:
                timestamp_str = entry['timestamp']
                try:
                    # Parse timestamp
                    timestamp = datetime.fromisoformat(timestamp_str.replace('T', ' ').replace('Z', ''))
                    age = now - timestamp
                    
                    # For test data, we allow any reasonable timestamp
                    # In production, you might want stricter validation
                    self.assertLess(age.days, 365, f"Data for {symbol} is more than a year old")
                    
                except ValueError:
                    self.fail(f"Invalid timestamp format for {symbol}: {timestamp_str}")


def run_data_validation_tests():
    """Run all data validation tests"""
    print("🔍 RUNNING DATA VALIDATION TESTS")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseDataValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestJSONDataValidation))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("📋 DATA VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  • {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  • {test}: {traceback.split('Exception:')[-1].strip()}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    if success:
        print("\n🎉 ALL DATA VALIDATION TESTS PASSED!")
    else:
        print("\n🚨 SOME DATA VALIDATION TESTS FAILED!")
    
    return success


if __name__ == '__main__':
    run_data_validation_tests()
