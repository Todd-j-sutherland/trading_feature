#!/usr/bin/env python3
"""
Unit Tests for Trading Microservices

This module contains comprehensive unit tests for all trading microservices,
focusing on individual component testing with proper mocking and isolation.

Author: Trading System Testing Team
Date: September 14, 2025
"""

import unittest
import asyncio
import json
import tempfile
import os
import sys
import sqlite3
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta

# Add services to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services'))

class TestBaseServiceCore(unittest.TestCase):
    """Core BaseService functionality tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_socket = "/tmp/test_base_service.sock"
        
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_socket):
            os.unlink(self.test_socket)
            
    @patch('redis.Redis')
    def test_base_service_initialization(self, mock_redis):
        """Test BaseService initialization with mocked Redis"""
        mock_redis.from_url.return_value.ping.return_value = True
        
        from base_service import BaseService
        
        service = BaseService("test-service", self.test_socket)
        
        # Test basic attributes
        self.assertEqual(service.service_name, "test-service")
        self.assertEqual(service.socket_path, self.test_socket)
        self.assertTrue(service.running)
        self.assertIsNotNone(service.health)
        
        # Test Redis connection attempt
        mock_redis.from_url.assert_called_once()
        
    @patch('redis.Redis')
    def test_health_check_format(self, mock_redis):
        """Test health check response format"""
        mock_redis.from_url.return_value.ping.return_value = True
        
        from base_service import BaseService
        
        service = BaseService("test-service")
        health = asyncio.run(service.health_check())
        
        # Verify required fields
        required_fields = ['service', 'status', 'uptime', 'memory_usage', 'handlers']
        for field in required_fields:
            self.assertIn(field, health)
            
        self.assertEqual(health['service'], 'test-service')
        
    @patch('redis.Redis')
    def test_method_registration(self, mock_redis):
        """Test method registration and handler storage"""
        mock_redis.from_url.return_value.ping.return_value = True
        
        from base_service import BaseService
        
        service = BaseService("test-service")
        
        async def test_handler():
            return {"result": "test"}
            
        service.register_handler("test_method", test_handler)
        
        self.assertIn("test_method", service.handlers)
        self.assertEqual(service.handlers["test_method"], test_handler)
        
    @patch('redis.Redis')
    def test_redis_connection_failure_handling(self, mock_redis):
        """Test handling of Redis connection failures"""
        mock_redis.from_url.side_effect = Exception("Redis connection failed")
        
        from base_service import BaseService
        
        service = BaseService("test-service")
        
        # Service should still initialize without Redis
        self.assertIsNone(service.redis_client)
        self.assertEqual(service.service_name, "test-service")
        
    @patch('redis.Redis')
    def test_event_publishing_without_redis(self, mock_redis):
        """Test event publishing when Redis is unavailable"""
        mock_redis.from_url.return_value = None
        
        from base_service import BaseService
        
        service = BaseService("test-service")
        service.redis_client = None
        
        result = service.publish_event("test_event", {"data": "test"})
        
        self.assertFalse(result)

class TestMarketDataServiceUnit(unittest.TestCase):
    """Unit tests for Market Data Service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_price_data = [95.0, 95.5, 94.8, 96.2, 95.8, 97.1, 96.5, 95.9, 96.8, 97.2]
        
    @patch('redis.Redis')
    @patch('requests.get')
    def test_alpha_vantage_api_call(self, mock_get, mock_redis):
        """Test Alpha Vantage API integration"""
        mock_redis.from_url.return_value.ping.return_value = True
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Global Quote": {
                "01. symbol": "CBA.AX",
                "05. price": "95.50",
                "06. volume": "1500000",
                "09. change": "+0.50",
                "10. change percent": "+0.53%"
            }
        }
        mock_get.return_value = mock_response
        
        from market_data_service import MarketDataService
        
        service = MarketDataService()
        
        # Test data retrieval
        result = asyncio.run(service._fetch_alpha_vantage_data("CBA.AX"))
        
        self.assertIsNotNone(result)
        self.assertIn('price', result)
        self.assertEqual(float(result['price']), 95.50)
        
        # Verify API was called with correct parameters
        mock_get.assert_called_once()
        call_args = mock_get.call_args[1]  # keyword arguments
        self.assertIn('params', call_args)
        self.assertEqual(call_args['params']['symbol'], 'CBA.AX')
        
    @patch('redis.Redis')
    def test_technical_indicators_calculation(self, mock_redis):
        """Test technical indicators calculation"""
        mock_redis.from_url.return_value.ping.return_value = True
        
        from market_data_service import MarketDataService
        
        service = MarketDataService()
        
        # Test RSI calculation
        rsi = service._calculate_rsi(self.sample_price_data)
        self.assertGreaterEqual(rsi, 0)
        self.assertLessEqual(rsi, 100)
        
        # Test MACD calculation
        macd = service._calculate_macd(self.sample_price_data)
        self.assertIsInstance(macd, float)
        
        # Test Bollinger Bands
        upper, lower = service._calculate_bollinger_bands(self.sample_price_data)
        self.assertGreater(upper, lower)
        
    @patch('redis.Redis')
    def test_data_validation(self, mock_redis):
        """Test market data validation logic"""
        mock_redis.from_url.return_value.ping.return_value = True
        
        from market_data_service import MarketDataService
        
        service = MarketDataService()
        
        # Valid data
        valid_data = {
            "price": 95.50,
            "volume": 1500000,
            "change": 0.50
        }
        self.assertTrue(service._validate_market_data(valid_data))
        
        # Invalid price (negative)
        invalid_price = {
            "price": -95.50,
            "volume": 1500000,
            "change": 0.50
        }
        self.assertFalse(service._validate_market_data(invalid_price))
        
        # Invalid volume (non-numeric)
        invalid_volume = {
            "price": 95.50,
            "volume": "invalid",
            "change": 0.50
        }
        self.assertFalse(service._validate_market_data(invalid_volume))
        
    @patch('redis.Redis')
    def test_caching_mechanism(self, mock_redis):
        """Test data caching functionality"""
        mock_redis_instance = Mock()
        mock_redis.from_url.return_value = mock_redis_instance
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.get.return_value = None  # No cached data
        
        from market_data_service import MarketDataService
        
        service = MarketDataService()
        
        # Test cache key generation
        cache_key = service._generate_cache_key("CBA.AX", "daily")
        self.assertEqual(cache_key, "market_data:CBA.AX:daily")
        
        # Test cache storage
        test_data = {"price": 95.50, "volume": 1500000}
        service._cache_market_data("CBA.AX", test_data, 300)  # 5 minutes
        
        # Verify Redis set was called
        mock_redis_instance.setex.assert_called_once()

class TestPredictionServiceUnit(unittest.TestCase):
    """Unit tests for Prediction Service"""
    
    @patch('redis.Redis')
    def test_prediction_confidence_calculation(self, mock_redis):
        """Test prediction confidence calculation logic"""
        mock_redis.from_url.return_value.ping.return_value = True
        
        from prediction_service import PredictionService
        
        service = PredictionService()
        
        # Mock data inputs
        tech_data = {
            "current_price": 95.50,
            "rsi": 65.2,
            "tech_score": 75
        }
        
        news_data = {
            "sentiment_score": 0.6,
            "news_confidence": 0.8,
            "news_quality_score": 0.7
        }
        
        volume_data = {
            "volume_trend": 0.15,
            "volume_quality_score": 0.8
        }
        
        market_data = {
            "context": "BULLISH",
            "buy_threshold": 0.70
        }
        
        # Test prediction calculation
        prediction = service.predictor.calculate_confidence(
            symbol="CBA.AX",
            tech_data=tech_data,
            news_data=news_data,
            volume_data=volume_data,
            market_data=market_data
        )
        
        # Verify prediction format
        self.assertIn('action', prediction)
        self.assertIn('confidence', prediction)
        self.assertIn('symbol', prediction)
        
        # Verify confidence range
        self.assertGreaterEqual(prediction['confidence'], 0.0)
        self.assertLessEqual(prediction['confidence'], 1.0)
        
        # Verify action is valid
        valid_actions = ['BUY', 'SELL', 'HOLD', 'STRONG_BUY', 'STRONG_SELL']
        self.assertIn(prediction['action'], valid_actions)
        
    @patch('redis.Redis')
    def test_prediction_caching(self, mock_redis):
        """Test prediction caching mechanism"""
        mock_redis.from_url.return_value.ping.return_value = True
        
        from prediction_service import PredictionService
        
        service = PredictionService()
        
        # Test cache storage
        prediction_data = {
            "symbol": "CBA.AX",
            "action": "BUY",
            "confidence": 0.85,
            "prediction_date": "2025-09-14"
        }
        
        # Add to cache
        cache_key = "prediction:CBA.AX"
        service.prediction_cache[cache_key] = (prediction_data, datetime.now().timestamp())
        
        # Test cache retrieval
        cached_prediction = asyncio.run(service.get_prediction("CBA.AX"))
        
        self.assertIn('cached', cached_prediction)
        self.assertTrue(cached_prediction['cached'])
        self.assertEqual(cached_prediction['symbol'], 'CBA.AX')
        self.assertEqual(cached_prediction['action'], 'BUY')
        
    @patch('redis.Redis')
    def test_buy_rate_calculation(self, mock_redis):
        """Test BUY rate calculation accuracy"""
        mock_redis.from_url.return_value.ping.return_value = True
        
        from prediction_service import PredictionService
        
        service = PredictionService()
        
        # Set up test data
        service.prediction_count = 20
        service.buy_signal_count = 14  # 70% buy rate
        
        buy_rate_result = asyncio.run(service.get_buy_rate())
        
        self.assertEqual(buy_rate_result['buy_rate'], 70.0)
        self.assertEqual(buy_rate_result['total_predictions'], 20)
        self.assertEqual(buy_rate_result['buy_signals'], 14)
        
    @patch('redis.Redis')
    def test_cache_cleanup(self, mock_redis):
        """Test prediction cache cleanup"""
        mock_redis.from_url.return_value.ping.return_value = True
        
        from prediction_service import PredictionService
        
        service = PredictionService()
        
        # Add test cache entries
        for i in range(5):
            cache_key = f"prediction:TEST{i}.AX"
            prediction_data = {"symbol": f"TEST{i}.AX", "action": "BUY", "confidence": 0.75}
            service.prediction_cache[cache_key] = (prediction_data, datetime.now().timestamp())
            
        # Verify cache has entries
        self.assertEqual(len(service.prediction_cache), 5)
        
        # Clear cache
        clear_result = asyncio.run(service.clear_cache())
        
        self.assertEqual(clear_result['cleared_entries'], 5)
        self.assertEqual(len(service.prediction_cache), 0)

class TestPaperTradingServiceUnit(unittest.TestCase):
    """Unit tests for Paper Trading Service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_db_path = tempfile.mktemp(suffix='.db')
        
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)
            
    @patch('redis.Redis')
    def test_portfolio_initialization(self, mock_redis):
        """Test portfolio initialization with starting cash"""
        mock_redis.from_url.return_value.ping.return_value = True
        
        from paper_trading_service import PaperTradingService
        
        service = PaperTradingService()
        
        # Test with different starting amounts
        portfolio_100k = service._initialize_portfolio(100000.0)
        self.assertEqual(portfolio_100k['cash'], 100000.0)
        self.assertEqual(portfolio_100k['total_value'], 100000.0)
        self.assertEqual(len(portfolio_100k['positions']), 0)
        
        portfolio_50k = service._initialize_portfolio(50000.0)
        self.assertEqual(portfolio_50k['cash'], 50000.0)
        
    @patch('redis.Redis')
    def test_trade_validation(self, mock_redis):
        """Test trade validation logic"""
        mock_redis.from_url.return_value.ping.return_value = True
        
        from paper_trading_service import PaperTradingService
        
        service = PaperTradingService()
        
        # Valid trade
        valid_trade = {
            "symbol": "CBA.AX",
            "action": "BUY",
            "quantity": 100,
            "price": 95.50
        }
        self.assertTrue(service._validate_trade(valid_trade))
        
        # Invalid symbol
        invalid_symbol = {
            "symbol": "",
            "action": "BUY", 
            "quantity": 100,
            "price": 95.50
        }
        self.assertFalse(service._validate_trade(invalid_symbol))
        
        # Invalid quantity
        invalid_quantity = {
            "symbol": "CBA.AX",
            "action": "BUY",
            "quantity": -100,
            "price": 95.50
        }
        self.assertFalse(service._validate_trade(invalid_quantity))
        
        # Invalid action
        invalid_action = {
            "symbol": "CBA.AX", 
            "action": "INVALID",
            "quantity": 100,
            "price": 95.50
        }
        self.assertFalse(service._validate_trade(invalid_action))
        
    @patch('redis.Redis')
    def test_risk_calculation(self, mock_redis):
        """Test risk calculation metrics"""
        mock_redis.from_url.return_value.ping.return_value = True
        
        from paper_trading_service import PaperTradingService
        
        service = PaperTradingService()
        
        # Mock portfolio with positions
        portfolio = {
            'cash': 20000.0,
            'total_value': 100000.0,
            'positions': [
                {'symbol': 'CBA.AX', 'quantity': 500, 'avg_price': 95.0, 'current_value': 47500.0},
                {'symbol': 'ANZ.AX', 'quantity': 1000, 'avg_price': 23.5, 'current_value': 23500.0},
                {'symbol': 'NAB.AX', 'quantity': 300, 'avg_price': 30.0, 'current_value': 9000.0}
            ]
        }
        
        risk_metrics = service._calculate_risk_metrics(portfolio)
        
        # Test calculated metrics
        self.assertIn('portfolio_diversity', risk_metrics)
        self.assertIn('cash_ratio', risk_metrics)
        self.assertIn('largest_position_pct', risk_metrics)
        
        # Verify calculations
        self.assertEqual(risk_metrics['cash_ratio'], 0.2)  # 20%
        self.assertEqual(risk_metrics['largest_position_pct'], 47.5)  # CBA position
        self.assertEqual(len(risk_metrics['position_sizes']), 3)
        
    @patch('redis.Redis')
    def test_performance_calculation(self, mock_redis):
        """Test portfolio performance calculation"""
        mock_redis.from_url.return_value.ping.return_value = True
        
        from paper_trading_service import PaperTradingService
        
        service = PaperTradingService()
        
        # Mock historical performance data
        performance_data = [
            {'date': '2025-09-01', 'total_value': 100000.0},
            {'date': '2025-09-07', 'total_value': 105000.0},
            {'date': '2025-09-14', 'total_value': 108000.0}
        ]
        
        performance_metrics = service._calculate_performance_metrics(performance_data)
        
        self.assertIn('total_return', performance_metrics)
        self.assertIn('weekly_return', performance_metrics)
        self.assertIn('daily_return', performance_metrics)
        
        # Verify total return calculation (8% gain)
        self.assertAlmostEqual(performance_metrics['total_return'], 8.0, places=1)

class TestSchedulerServiceUnit(unittest.TestCase):
    """Unit tests for Scheduler Service"""
    
    @patch('redis.Redis')
    def test_job_scheduling(self, mock_redis):
        """Test job scheduling functionality"""
        mock_redis.from_url.return_value.ping.return_value = True
        
        from scheduler_service import SchedulerService
        
        service = SchedulerService()
        
        # Test job creation
        job_result = asyncio.run(service.schedule_market_aware_job(
            job_id="test_job_1",
            job_type="morning_analysis",
            params={"symbols": ["CBA.AX", "ANZ.AX"]}
        ))
        
        self.assertIn('id', job_result)
        self.assertIn('type', job_result)
        self.assertIn('schedule_time', job_result)
        self.assertEqual(job_result['id'], 'test_job_1')
        self.assertEqual(job_result['type'], 'morning_analysis')
        
        # Verify job is stored
        self.assertIn('test_job_1', service.jobs)
        
    @patch('redis.Redis')
    def test_market_hours_awareness(self, mock_redis):
        """Test market hours awareness in scheduling"""
        mock_redis.from_url.return_value.ping.return_value = True
        
        from scheduler_service import SchedulerService
        
        service = SchedulerService()
        
        # Test different job types get appropriate schedule times
        morning_job = asyncio.run(service.schedule_market_aware_job(
            job_id="morning_test",
            job_type="morning_analysis"
        ))
        
        evening_job = asyncio.run(service.schedule_market_aware_job(
            job_id="evening_test", 
            job_type="evening_analysis"
        ))
        
        prediction_job = asyncio.run(service.schedule_market_aware_job(
            job_id="prediction_test",
            job_type="prediction_generation"
        ))
        
        # Verify appropriate scheduling times
        self.assertEqual(morning_job['schedule_time'], "09:30")
        self.assertEqual(evening_job['schedule_time'], "17:00") 
        self.assertEqual(prediction_job['schedule_time'], "09:45")
        
    @patch('redis.Redis')
    def test_job_dependency_management(self, mock_redis):
        """Test job dependency handling"""
        mock_redis.from_url.return_value.ping.return_value = True
        
        from scheduler_service import SchedulerService
        
        service = SchedulerService()
        
        # Create dependent jobs
        parent_job = asyncio.run(service.schedule_market_aware_job(
            job_id="parent_job",
            job_type="prediction_generation"
        ))
        
        dependent_job = asyncio.run(service.schedule_dependent_job(
            job_id="dependent_job",
            job_type="paper_trading_execution",
            depends_on=["parent_job"]
        ))
        
        self.assertIn('depends_on', dependent_job)
        self.assertEqual(dependent_job['depends_on'], ["parent_job"])

class TestMLModelServiceUnit(unittest.TestCase):
    """Unit tests for ML Model Service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_model_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.test_model_dir)
        
    @patch('redis.Redis')
    def test_model_loading(self, mock_redis):
        """Test model loading functionality"""
        mock_redis.from_url.return_value.ping.return_value = True
        
        from ml_model_service import MLModelService
        
        service = MLModelService()
        
        # Mock model file
        import pickle
        mock_model = {"type": "test_model", "version": "1.0"}
        model_path = os.path.join(self.test_model_dir, "test_model.pkl")
        
        with open(model_path, 'wb') as f:
            pickle.dump(mock_model, f)
            
        # Test loading
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', unittest.mock.mock_open()), \
             patch('pickle.load', return_value=mock_model):
            
            result = asyncio.run(service.load_model("test_model"))
            
            self.assertIn('model_loaded', result)
            self.assertTrue(result['model_loaded'])
            
    @patch('redis.Redis') 
    def test_model_prediction(self, mock_redis):
        """Test model prediction functionality"""
        mock_redis.from_url.return_value.ping.return_value = True
        
        from ml_model_service import MLModelService
        
        service = MLModelService()
        
        # Mock trained model
        mock_model = Mock()
        mock_model.predict.return_value = [0.85]  # Prediction confidence
        
        service.active_models["test_model"] = {
            'model': mock_model,
            'loaded_at': datetime.now(),
            'symbol': None
        }
        
        # Test prediction
        features = {
            'rsi': 65.2,
            'macd': 0.85,
            'volume_trend': 0.15,
            'sentiment': 0.6
        }
        
        result = asyncio.run(service.predict("test_model", features))
        
        self.assertIn('prediction', result)
        self.assertIn('model', result)
        self.assertEqual(result['prediction'], [0.85])
        self.assertEqual(result['model'], 'test_model')

def run_unit_tests():
    """Run all unit tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestBaseServiceCore,
        TestMarketDataServiceUnit,
        TestPredictionServiceUnit, 
        TestPaperTradingServiceUnit,
        TestSchedulerServiceUnit,
        TestMLModelServiceUnit
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
        
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result

if __name__ == "__main__":
    result = run_unit_tests()
    
    # Exit with appropriate code
    if result.failures or result.errors:
        sys.exit(1)
    else:
        print("\n✅ All unit tests passed!")
        sys.exit(0)
