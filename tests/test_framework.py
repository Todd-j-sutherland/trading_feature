#!/usr/bin/env python3
"""
Comprehensive Testing Framework for Trading Microservices

This module provides a complete testing infrastructure including unit tests,
integration tests, performance tests, and automated testing pipeline for
continuous validation of the trading microservices architecture.

Features:
- Unit testing framework with mocking capabilities
- Integration testing for service communication
- Performance and load testing
- Test data management and fixtures
- Automated test discovery and execution
- Continuous integration pipeline support
- Test reporting and metrics
- Mock services for isolated testing

Author: Trading System Testing Team
Date: September 14, 2025
"""

import unittest
import asyncio
import json
import time
import tempfile
import shutil
import sqlite3
import os
import sys
import subprocess
import threading
import socket
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass
import concurrent.futures
import logging
import psutil

# Add services to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services'))

@dataclass
class TestResult:
    """Test execution result"""
    test_name: str
    status: str  # passed, failed, skipped, error
    duration: float
    error_message: Optional[str] = None
    details: Optional[Dict] = None

@dataclass
class TestSuite:
    """Test suite configuration"""
    name: str
    test_files: List[str]
    setup_required: List[str]
    teardown_required: List[str]
    parallel_execution: bool = False

class TestDataManager:
    """Manages test data and fixtures"""
    
    def __init__(self, test_data_dir: str = "tests/data"):
        self.test_data_dir = Path(test_data_dir)
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Test databases
        self.test_db_dir = self.test_data_dir / "databases"
        self.test_db_dir.mkdir(exist_ok=True)
        
    def create_test_database(self, db_name: str, schema: str = None) -> str:
        """Create a test database with optional schema"""
        db_path = self.test_db_dir / f"test_{db_name}"
        
        # Remove existing test database
        if db_path.exists():
            db_path.unlink()
            
        conn = sqlite3.connect(str(db_path))
        
        if schema:
            conn.executescript(schema)
        else:
            # Default prediction schema
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    prediction_date DATE NOT NULL,
                    action TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_id INTEGER,
                    actual_action TEXT,
                    accuracy REAL,
                    profit_loss REAL,
                    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (prediction_id) REFERENCES predictions (id)
                );
            """)
            
        conn.close()
        return str(db_path)
        
    def load_test_fixtures(self, fixture_name: str) -> Dict[str, Any]:
        """Load test fixture data"""
        fixture_path = self.test_data_dir / "fixtures" / f"{fixture_name}.json"
        
        if fixture_path.exists():
            with open(fixture_path, 'r') as f:
                return json.load(f)
        else:
            # Create default fixtures
            return self._create_default_fixtures(fixture_name)
            
    def _create_default_fixtures(self, fixture_name: str) -> Dict[str, Any]:
        """Create default test fixtures"""
        fixtures = {
            "market_data": {
                "CBA.AX": {
                    "current_price": 95.50,
                    "volume": 1500000,
                    "technical_indicators": {
                        "rsi": 65.2,
                        "macd": 0.85,
                        "bollinger_upper": 98.0,
                        "bollinger_lower": 92.0
                    }
                },
                "ANZ.AX": {
                    "current_price": 23.45,
                    "volume": 2100000,
                    "technical_indicators": {
                        "rsi": 58.7,
                        "macd": -0.32,
                        "bollinger_upper": 24.2,
                        "bollinger_lower": 22.1
                    }
                }
            },
            "predictions": [
                {
                    "symbol": "CBA.AX",
                    "action": "BUY",
                    "confidence": 0.85,
                    "prediction_date": "2025-09-14",
                    "details": {"tech_score": 75, "sentiment_score": 0.6}
                },
                {
                    "symbol": "ANZ.AX", 
                    "action": "HOLD",
                    "confidence": 0.65,
                    "prediction_date": "2025-09-14",
                    "details": {"tech_score": 55, "sentiment_score": 0.1}
                }
            ],
            "news_data": [
                {
                    "symbol": "CBA.AX",
                    "headline": "Commonwealth Bank reports strong quarterly results",
                    "sentiment": 0.8,
                    "confidence": 0.9,
                    "published_at": "2025-09-14T10:00:00Z"
                }
            ]
        }
        
        # Save fixture
        fixture_path = self.test_data_dir / "fixtures" / f"{fixture_name}.json"
        fixture_path.parent.mkdir(exist_ok=True)
        
        with open(fixture_path, 'w') as f:
            json.dump(fixtures, f, indent=2)
            
        return fixtures

class MockServiceManager:
    """Manages mock services for isolated testing"""
    
    def __init__(self):
        self.mock_services = {}
        self.mock_servers = {}
        
    async def start_mock_service(self, service_name: str, mock_responses: Dict[str, Any]) -> str:
        """Start a mock service with predefined responses"""
        socket_path = f"/tmp/test_trading_{service_name}.sock"
        
        # Remove existing socket
        if os.path.exists(socket_path):
            os.unlink(socket_path)
            
        # Create mock server
        server = await asyncio.start_unix_server(
            lambda reader, writer: self._handle_mock_request(reader, writer, mock_responses),
            socket_path
        )
        
        self.mock_servers[service_name] = server
        self.mock_services[service_name] = socket_path
        
        return socket_path
        
    async def _handle_mock_request(self, reader, writer, mock_responses: Dict[str, Any]):
        """Handle mock service requests"""
        try:
            data = await reader.read(8192)
            if not data:
                return
                
            request = json.loads(data.decode())
            method = request.get('method', 'unknown')
            
            # Return mock response
            if method in mock_responses:
                response = {
                    'status': 'success',
                    'result': mock_responses[method],
                    'request_id': request.get('request_id', 0)
                }
            else:
                response = {
                    'status': 'error',
                    'error': f'Mock method not implemented: {method}',
                    'request_id': request.get('request_id', 0)
                }
                
            writer.write(json.dumps(response).encode())
            await writer.drain()
            
        except Exception as e:
            error_response = {
                'status': 'error',
                'error': str(e),
                'request_id': 0
            }
            writer.write(json.dumps(error_response).encode())
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()
            
    async def stop_mock_service(self, service_name: str):
        """Stop a mock service"""
        if service_name in self.mock_servers:
            server = self.mock_servers[service_name]
            server.close()
            await server.wait_closed()
            
            del self.mock_servers[service_name]
            
        if service_name in self.mock_services:
            socket_path = self.mock_services[service_name]
            if os.path.exists(socket_path):
                os.unlink(socket_path)
            del self.mock_services[service_name]
            
    async def stop_all_mock_services(self):
        """Stop all mock services"""
        for service_name in list(self.mock_services.keys()):
            await self.stop_mock_service(service_name)

class BaseTestCase(unittest.TestCase):
    """Base test case with common setup and utilities"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class"""
        cls.test_data = TestDataManager()
        cls.mock_manager = MockServiceManager()
        
        # Setup test logging
        logging.basicConfig(level=logging.DEBUG)
        cls.logger = logging.getLogger(cls.__name__)
        
    @classmethod
    def tearDownClass(cls):
        """Clean up test class"""
        # Clean up mock services
        if hasattr(cls, 'mock_manager'):
            asyncio.run(cls.mock_manager.stop_all_mock_services())
            
    def setUp(self):
        """Set up individual test"""
        self.start_time = time.time()
        
    def tearDown(self):
        """Clean up individual test"""
        self.execution_time = time.time() - self.start_time
        
    def assert_service_response(self, response: Dict, expected_status: str = 'success'):
        """Assert service response format"""
        self.assertIn('status', response)
        self.assertEqual(response['status'], expected_status)
        
        if expected_status == 'success':
            self.assertIn('result', response)
        else:
            self.assertIn('error', response)
            
    def assert_prediction_format(self, prediction: Dict):
        """Assert prediction data format"""
        required_fields = ['symbol', 'action', 'confidence', 'prediction_date']
        for field in required_fields:
            self.assertIn(field, prediction)
            
        # Validate action values
        self.assertIn(prediction['action'], ['BUY', 'SELL', 'HOLD', 'STRONG_BUY', 'STRONG_SELL'])
        
        # Validate confidence range
        self.assertGreaterEqual(prediction['confidence'], 0.0)
        self.assertLessEqual(prediction['confidence'], 1.0)

class TestBaseService(BaseTestCase):
    """Test BaseService framework functionality"""
    
    def test_base_service_initialization(self):
        """Test BaseService initialization"""
        from base_service import BaseService
        
        service = BaseService("test-service", socket_path="/tmp/test_service.sock")
        
        self.assertEqual(service.service_name, "test-service")
        self.assertEqual(service.socket_path, "/tmp/test_service.sock")
        self.assertIsNotNone(service.health)
        
    def test_service_health_check(self):
        """Test service health check functionality"""
        from base_service import BaseService
        
        service = BaseService("test-service")
        
        # Test health check
        health = asyncio.run(service.health_check())
        
        self.assertIn('service', health)
        self.assertIn('status', health)
        self.assertIn('uptime', health)
        self.assertEqual(health['service'], 'test-service')
        
    def test_service_method_registration(self):
        """Test method registration"""
        from base_service import BaseService
        
        service = BaseService("test-service")
        
        async def test_method():
            return {"test": "result"}
            
        service.register_handler("test_method", test_method)
        
        self.assertIn("test_method", service.handlers)
        
    def test_redis_connection_handling(self):
        """Test Redis connection with mocking"""
        from base_service import BaseService
        
        with patch('redis.Redis') as mock_redis:
            mock_redis.from_url.return_value.ping.return_value = True
            
            service = BaseService("test-service")
            
            self.assertIsNotNone(service.redis_client)
            mock_redis.from_url.assert_called_once()

class TestMarketDataService(BaseTestCase):
    """Test Market Data Service functionality"""
    
    def setUp(self):
        super().setUp()
        self.fixtures = self.test_data.load_test_fixtures("market_data")
        
    def test_market_data_retrieval(self):
        """Test market data retrieval with mocked APIs"""
        with patch('requests.get') as mock_get:
            # Mock API response
            mock_response = Mock()
            mock_response.json.return_value = {
                "Global Quote": {
                    "05. price": "95.50",
                    "06. volume": "1500000",
                    "09. change": "+0.50"
                }
            }
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            from market_data_service import MarketDataService
            
            service = MarketDataService()
            
            # Test data retrieval
            result = asyncio.run(service.get_market_data("CBA.AX"))
            
            self.assertIn('technical', result)
            self.assertIn('volume', result)
            self.assertIn('market_context', result)
            
    def test_technical_indicators_calculation(self):
        """Test technical indicators calculation"""
        from market_data_service import MarketDataService
        
        service = MarketDataService()
        
        # Mock price data
        price_data = [95.0, 95.5, 94.8, 96.2, 95.8, 97.1, 96.5]
        
        indicators = service._calculate_technical_indicators(price_data)
        
        self.assertIn('rsi', indicators)
        self.assertIn('macd', indicators)
        self.assertGreaterEqual(indicators['rsi'], 0)
        self.assertLessEqual(indicators['rsi'], 100)
        
    def test_data_validation(self):
        """Test market data validation"""
        from market_data_service import MarketDataService
        
        service = MarketDataService()
        
        # Valid data
        valid_data = {
            "price": 95.50,
            "volume": 1500000,
            "change": 0.50
        }
        
        self.assertTrue(service._validate_market_data(valid_data))
        
        # Invalid data
        invalid_data = {
            "price": -95.50,  # Negative price
            "volume": "invalid",  # Non-numeric volume
        }
        
        self.assertFalse(service._validate_market_data(invalid_data))

class TestPredictionService(BaseTestCase):
    """Test Prediction Service functionality"""
    
    def setUp(self):
        super().setUp()
        self.fixtures = self.test_data.load_test_fixtures("predictions")
        
    async def test_prediction_generation(self):
        """Test prediction generation with mock dependencies"""
        # Setup mock services
        mock_responses = {
            "get_market_data": {
                "technical": {"current_price": 95.50, "rsi": 65.2},
                "volume": {"volume_trend": 0.15, "volume_quality_score": 0.8},
                "market_context": {"context": "BULLISH", "buy_threshold": 0.70}
            }
        }
        
        await self.mock_manager.start_mock_service("market-data", mock_responses)
        
        sentiment_responses = {
            "analyze_sentiment": {
                "sentiment_score": 0.6,
                "news_confidence": 0.8,
                "news_quality_score": 0.7
            }
        }
        
        await self.mock_manager.start_mock_service("sentiment", sentiment_responses)
        
        from prediction_service import PredictionService
        
        service = PredictionService()
        
        # Test prediction generation
        result = await service.generate_single_prediction("CBA.AX")
        
        self.assert_prediction_format(result)
        self.assertEqual(result['symbol'], 'CBA.AX')
        
    def test_prediction_caching(self):
        """Test prediction caching mechanism"""
        from prediction_service import PredictionService
        
        service = PredictionService()
        
        # Mock prediction data
        prediction_data = {
            "symbol": "CBA.AX",
            "action": "BUY", 
            "confidence": 0.85,
            "prediction_date": "2025-09-14"
        }
        
        # Cache prediction
        cache_key = "prediction:CBA.AX"
        service.prediction_cache[cache_key] = (prediction_data, time.time())
        
        # Test cache retrieval
        cached = asyncio.run(service.get_prediction("CBA.AX"))
        
        self.assertIn('cached', cached)
        self.assertTrue(cached['cached'])
        self.assertEqual(cached['symbol'], 'CBA.AX')
        
    def test_buy_rate_calculation(self):
        """Test BUY rate calculation"""
        from prediction_service import PredictionService
        
        service = PredictionService()
        
        # Mock prediction counts
        service.prediction_count = 10
        service.buy_signal_count = 7
        
        result = asyncio.run(service.get_buy_rate())
        
        self.assertEqual(result['buy_rate'], 70.0)
        self.assertEqual(result['total_predictions'], 10)
        self.assertEqual(result['buy_signals'], 7)

class TestPaperTradingService(BaseTestCase):
    """Test Paper Trading Service functionality"""
    
    def setUp(self):
        super().setUp()
        self.test_db = self.test_data.create_test_database("paper_trading")
        
    def test_portfolio_initialization(self):
        """Test portfolio initialization"""
        from paper_trading_service import PaperTradingService
        
        service = PaperTradingService()
        
        portfolio = service._initialize_portfolio(100000.0)  # $100k starting
        
        self.assertEqual(portfolio['cash'], 100000.0)
        self.assertEqual(portfolio['total_value'], 100000.0)
        self.assertEqual(len(portfolio['positions']), 0)
        
    def test_trade_execution(self):
        """Test trade execution logic"""
        from paper_trading_service import PaperTradingService
        
        service = PaperTradingService()
        
        # Mock market price
        with patch.object(service, '_get_current_price', return_value=95.50):
            trade_result = asyncio.run(service.execute_trade(
                symbol="CBA.AX",
                action="BUY",
                quantity=100
            ))
            
            self.assertIn('trade_id', trade_result)
            self.assertIn('status', trade_result)
            self.assertEqual(trade_result['symbol'], 'CBA.AX')
            self.assertEqual(trade_result['action'], 'BUY')
            self.assertEqual(trade_result['quantity'], 100)
            
    def test_risk_assessment(self):
        """Test risk assessment calculations"""
        from paper_trading_service import PaperTradingService
        
        service = PaperTradingService()
        
        # Mock portfolio
        portfolio = {
            'cash': 50000.0,
            'total_value': 100000.0,
            'positions': [
                {'symbol': 'CBA.AX', 'quantity': 500, 'avg_price': 95.0},
                {'symbol': 'ANZ.AX', 'quantity': 1000, 'avg_price': 23.5}
            ]
        }
        
        risk_metrics = service._calculate_risk_metrics(portfolio)
        
        self.assertIn('portfolio_diversity', risk_metrics)
        self.assertIn('cash_ratio', risk_metrics)
        self.assertIn('largest_position_pct', risk_metrics)

class TestIntegrationScenarios(BaseTestCase):
    """Test end-to-end integration scenarios"""
    
    async def test_full_prediction_pipeline(self):
        """Test complete prediction pipeline"""
        # Setup mock services
        market_data_responses = {
            "get_market_data": {
                "technical": {"current_price": 95.50, "rsi": 65.2, "tech_score": 75},
                "volume": {"volume_trend": 0.15, "volume_quality_score": 0.8},
                "market_context": {"context": "BULLISH", "buy_threshold": 0.70}
            }
        }
        
        sentiment_responses = {
            "analyze_sentiment": {
                "sentiment_score": 0.6,
                "news_confidence": 0.8,
                "news_quality_score": 0.7
            }
        }
        
        await self.mock_manager.start_mock_service("market-data", market_data_responses)
        await self.mock_manager.start_mock_service("sentiment", sentiment_responses)
        
        from prediction_service import PredictionService
        
        prediction_service = PredictionService()
        
        # Test full pipeline
        result = await prediction_service.generate_predictions(["CBA.AX", "ANZ.AX"])
        
        self.assertIn('predictions', result)
        self.assertIn('summary', result)
        
        predictions = result['predictions']
        self.assertIn('CBA.AX', predictions)
        self.assert_prediction_format(predictions['CBA.AX'])
        
    async def test_paper_trading_integration(self):
        """Test paper trading with prediction integration"""
        # Setup mock prediction service
        prediction_responses = {
            "generate_single_prediction": {
                "symbol": "CBA.AX",
                "action": "BUY",
                "confidence": 0.85,
                "prediction_date": "2025-09-14"
            }
        }
        
        await self.mock_manager.start_mock_service("prediction", prediction_responses)
        
        from paper_trading_service import PaperTradingService
        
        trading_service = PaperTradingService()
        
        # Test automated trading based on predictions
        result = await trading_service.execute_prediction_trade("CBA.AX")
        
        self.assertIn('trade_executed', result)
        self.assertIn('prediction_used', result)

class PerformanceTestCase(BaseTestCase):
    """Performance and load testing"""
    
    def test_prediction_service_performance(self):
        """Test prediction service under load"""
        from prediction_service import PredictionService
        
        service = PredictionService()
        
        # Mock dependencies
        with patch.object(service, 'call_service') as mock_call:
            mock_call.return_value = {
                "technical": {"rsi": 65.2, "tech_score": 75},
                "sentiment_score": 0.6
            }
            
            start_time = time.time()
            
            # Generate multiple predictions
            symbols = ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX"] * 25  # 100 predictions
            
            result = asyncio.run(service.generate_predictions(symbols))
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Performance assertions
            self.assertLess(execution_time, 30.0)  # Should complete within 30 seconds
            self.assertEqual(len(result['predictions']), 100)
            
            # Calculate predictions per second
            predictions_per_second = 100 / execution_time
            self.assertGreater(predictions_per_second, 3.0)  # At least 3 predictions/second
            
    def test_memory_usage(self):
        """Test memory usage under load"""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Create large dataset
        large_predictions = []
        for i in range(1000):
            prediction = {
                'symbol': f'TEST{i:03d}.AX',
                'action': 'BUY',
                'confidence': 0.75,
                'details': {'data': 'x' * 1000}  # 1KB per prediction
            }
            large_predictions.append(prediction)
            
        peak_memory = process.memory_info().rss
        
        # Clean up
        del large_predictions
        gc.collect()
        
        final_memory = process.memory_info().rss
        
        # Memory should not increase dramatically
        memory_increase = peak_memory - initial_memory
        memory_mb = memory_increase / (1024 * 1024)
        
        self.assertLess(memory_mb, 50)  # Should not use more than 50MB
        
        # Memory should be released after cleanup
        memory_after_cleanup = final_memory - initial_memory
        cleanup_ratio = memory_after_cleanup / memory_increase
        
        self.assertLess(cleanup_ratio, 0.3)  # At least 70% memory should be released

class TestRunner:
    """Comprehensive test runner with reporting"""
    
    def __init__(self):
        self.test_results = []
        self.test_suites = [
            TestSuite("unit_tests", [
                "TestBaseService",
                "TestMarketDataService", 
                "TestPredictionService",
                "TestPaperTradingService"
            ], [], []),
            TestSuite("integration_tests", [
                "TestIntegrationScenarios"
            ], ["redis"], ["cleanup_mock_services"]),
            TestSuite("performance_tests", [
                "PerformanceTestCase"
            ], [], [])
        ]
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites"""
        overall_start = time.time()
        suite_results = {}
        
        for test_suite in self.test_suites:
            print(f"\n🧪 Running {test_suite.name}...")
            
            suite_result = self._run_test_suite(test_suite)
            suite_results[test_suite.name] = suite_result
            
            print(f"✅ {test_suite.name}: {suite_result['passed']}/{suite_result['total']} tests passed")
            
        overall_duration = time.time() - overall_start
        
        # Generate comprehensive report
        report = self._generate_test_report(suite_results, overall_duration)
        
        return report
        
    def _run_test_suite(self, test_suite: TestSuite) -> Dict[str, Any]:
        """Run a specific test suite"""
        suite_start = time.time()
        
        # Setup
        for setup_item in test_suite.setup_required:
            self._setup_requirement(setup_item)
            
        # Run tests
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        for test_class_name in test_suite.test_files:
            test_class = globals().get(test_class_name)
            if test_class:
                tests = loader.loadTestsFromTestCase(test_class)
                suite.addTests(tests)
                
        # Execute tests
        runner = unittest.TextTestRunner(verbosity=2, stream=open(os.devnull, 'w'))
        result = runner.run(suite)
        
        # Teardown
        for teardown_item in test_suite.teardown_required:
            self._teardown_requirement(teardown_item)
            
        suite_duration = time.time() - suite_start
        
        return {
            'total': result.testsRun,
            'passed': result.testsRun - len(result.failures) - len(result.errors),
            'failed': len(result.failures),
            'errors': len(result.errors),
            'duration': suite_duration,
            'failures': [str(f[1]) for f in result.failures],
            'error_details': [str(e[1]) for e in result.errors]
        }
        
    def _setup_requirement(self, requirement: str):
        """Setup test requirement"""
        if requirement == "redis":
            # Check if Redis is running
            try:
                import redis
                r = redis.Redis()
                r.ping()
            except:
                print("⚠️ Redis not available - some tests may fail")
                
    def _teardown_requirement(self, requirement: str):
        """Teardown test requirement"""
        if requirement == "cleanup_mock_services":
            # Cleanup mock services
            pass
            
    def _generate_test_report(self, suite_results: Dict, overall_duration: float) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = sum(suite['total'] for suite in suite_results.values())
        total_passed = sum(suite['passed'] for suite in suite_results.values())
        total_failed = sum(suite['failed'] for suite in suite_results.values())
        total_errors = sum(suite['errors'] for suite in suite_results.values())
        
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'overall_duration': overall_duration,
            'summary': {
                'total_tests': total_tests,
                'passed': total_passed,
                'failed': total_failed,
                'errors': total_errors,
                'success_rate': success_rate
            },
            'suite_results': suite_results,
            'recommendations': []
        }
        
        # Add recommendations
        if success_rate < 90:
            report['recommendations'].append("Test success rate below 90% - investigate failures")
            
        if overall_duration > 300:  # 5 minutes
            report['recommendations'].append("Test execution time excessive - optimize slow tests")
            
        if total_errors > 0:
            report['recommendations'].append("Test errors detected - fix test infrastructure issues")
            
        return report
        
    def save_test_report(self, report: Dict, filename: str = None):
        """Save test report to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_report_{timestamp}.json"
            
        report_path = Path("tests") / "reports" / filename
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"📊 Test report saved: {report_path}")

def main():
    """Main test execution entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Trading System Test Framework")
    parser.add_argument('--suite', choices=['unit', 'integration', 'performance', 'all'], 
                       default='all', help='Test suite to run')
    parser.add_argument('--report', action='store_true', help='Generate detailed report')
    parser.add_argument('--parallel', action='store_true', help='Run tests in parallel')
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.suite == 'all':
        report = runner.run_all_tests()
    else:
        # Run specific suite
        suite_map = {
            'unit': runner.test_suites[0],
            'integration': runner.test_suites[1], 
            'performance': runner.test_suites[2]
        }
        
        suite = suite_map[args.suite]
        suite_result = runner._run_test_suite(suite)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'suite_results': {args.suite: suite_result},
            'summary': suite_result
        }
        
    # Display results
    print(f"\n🎯 TEST RESULTS SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Errors: {report['summary']['errors']}")
    print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
    
    if args.report:
        runner.save_test_report(report)
        
    # Exit with appropriate code
    if report['summary']['failed'] > 0 or report['summary']['errors'] > 0:
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
