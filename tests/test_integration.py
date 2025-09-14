#!/usr/bin/env python3
"""
Integration Tests for Trading Microservices

This module contains comprehensive integration tests for the trading microservices,
focusing on service-to-service communication, end-to-end workflows, and 
system integration scenarios.

Author: Trading System Testing Team
Date: September 14, 2025
"""

import unittest
import asyncio
import json
import tempfile
import os
import sys
import time
import subprocess
import socket
import threading
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

# Add services to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services'))

class ServiceTestHarness:
    """Test harness for managing test services"""
    
    def __init__(self):
        self.running_services = {}
        self.test_sockets = {}
        
    async def start_test_service(self, service_name: str, service_class, **kwargs):
        """Start a service for testing"""
        try:
            service_instance = service_class(**kwargs)
            
            # Use test socket path
            test_socket = f"/tmp/test_trading_{service_name}.sock"
            service_instance.socket_path = test_socket
            
            # Start service in background
            task = asyncio.create_task(service_instance.start_server())
            
            # Wait for service to be ready
            await asyncio.sleep(2)
            
            self.running_services[service_name] = {
                'instance': service_instance,
                'task': task,
                'socket_path': test_socket
            }
            
            self.test_sockets[service_name] = test_socket
            
            return service_instance
            
        except Exception as e:
            print(f"Failed to start test service {service_name}: {e}")
            raise
            
    async def stop_test_service(self, service_name: str):
        """Stop a test service"""
        if service_name in self.running_services:
            service_info = self.running_services[service_name]
            
            # Stop the service
            service_info['instance'].running = False
            service_info['task'].cancel()
            
            try:
                await service_info['task']
            except asyncio.CancelledError:
                pass
                
            # Clean up socket
            socket_path = service_info['socket_path']
            if os.path.exists(socket_path):
                os.unlink(socket_path)
                
            del self.running_services[service_name]
            if service_name in self.test_sockets:
                del self.test_sockets[service_name]
                
    async def stop_all_services(self):
        """Stop all test services"""
        for service_name in list(self.running_services.keys()):
            await self.stop_test_service(service_name)
            
    async def call_service(self, service_name: str, method: str, **params):
        """Call a test service method"""
        if service_name not in self.test_sockets:
            raise Exception(f"Test service {service_name} not running")
            
        socket_path = self.test_sockets[service_name]
        
        try:
            reader, writer = await asyncio.open_unix_connection(socket_path)
            
            request = {
                'method': method,
                'params': params,
                'timestamp': time.time()
            }
            
            writer.write(json.dumps(request).encode())
            await writer.drain()
            
            response_data = await reader.read(32768)
            response = json.loads(response_data.decode())
            
            writer.close()
            await writer.wait_closed()
            
            return response
            
        except Exception as e:
            raise Exception(f"Service call failed: {e}")

class TestServiceCommunication(unittest.TestCase):
    """Test inter-service communication"""
    
    def setUp(self):
        """Set up test harness"""
        self.harness = ServiceTestHarness()
        
    def tearDown(self):
        """Clean up test harness"""
        asyncio.run(self.harness.stop_all_services())
        
    def test_base_service_socket_communication(self):
        """Test basic Unix socket communication"""
        from base_service import BaseService
        
        async def run_test():
            # Start test service
            await self.harness.start_test_service("base-test", BaseService, service_name="base-test")
            
            # Test health check
            response = await self.harness.call_service("base-test", "health")
            
            self.assertEqual(response['status'], 'success')
            self.assertIn('result', response)
            self.assertEqual(response['result']['service'], 'base-test')
            
        asyncio.run(run_test())
        
    def test_service_to_service_calls(self):
        """Test service-to-service method calls"""
        from base_service import BaseService
        
        async def run_test():
            # Start two test services
            service1 = await self.harness.start_test_service("service1", BaseService, service_name="service1")
            service2 = await self.harness.start_test_service("service2", BaseService, service_name="service2")
            
            # Add custom method to service2
            async def custom_method(data):
                return {"processed": data, "service": "service2"}
                
            service2.register_handler("custom_method", custom_method)
            
            # Service1 calls service2
            service1.socket_path = self.harness.test_sockets["service1"]
            result = await service1.call_service("service2", "custom_method", data="test_data")
            
            self.assertEqual(result['processed'], 'test_data')
            self.assertEqual(result['service'], 'service2')
            
        asyncio.run(run_test())
        
    def test_error_handling_in_communication(self):
        """Test error handling in service communication"""
        from base_service import BaseService
        
        async def run_test():
            # Start test service
            await self.harness.start_test_service("error-test", BaseService, service_name="error-test")
            
            # Test calling non-existent method
            response = await self.harness.call_service("error-test", "non_existent_method")
            
            self.assertEqual(response['status'], 'error')
            self.assertIn('error', response)
            self.assertIn('Unknown method', response['error'])
            
        asyncio.run(run_test())

class TestPredictionWorkflow(unittest.TestCase):
    """Test end-to-end prediction workflow"""
    
    def setUp(self):
        """Set up test harness"""
        self.harness = ServiceTestHarness()
        
    def tearDown(self):
        """Clean up test harness"""
        asyncio.run(self.harness.stop_all_services())
        
    @patch('redis.Redis')
    @patch('requests.get')
    def test_full_prediction_pipeline(self, mock_get, mock_redis):
        """Test complete prediction generation pipeline"""
        # Mock Redis
        mock_redis.from_url.return_value.ping.return_value = True
        
        # Mock market data API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Global Quote": {
                "01. symbol": "CBA.AX",
                "05. price": "95.50",
                "06. volume": "1500000",
                "09. change": "+0.50"
            }
        }
        mock_get.return_value = mock_response
        
        async def run_test():
            from market_data_service import MarketDataService
            from sentiment_service import SentimentAnalysisService  
            from prediction_service import PredictionService
            
            # Start dependent services
            await self.harness.start_test_service("market-data", MarketDataService)
            await self.harness.start_test_service("sentiment", SentimentAnalysisService)
            await self.harness.start_test_service("prediction", PredictionService)
            
            # Wait for services to initialize
            await asyncio.sleep(3)
            
            # Test market data retrieval
            market_response = await self.harness.call_service("market-data", "get_market_data", symbol="CBA.AX")
            
            self.assertEqual(market_response['status'], 'success')
            self.assertIn('technical', market_response['result'])
            
            # Test sentiment analysis
            sentiment_response = await self.harness.call_service("sentiment", "analyze_sentiment", symbol="CBA.AX")
            
            self.assertEqual(sentiment_response['status'], 'success')
            self.assertIn('sentiment_score', sentiment_response['result'])
            
            # Test prediction generation
            prediction_response = await self.harness.call_service("prediction", "generate_single_prediction", symbol="CBA.AX")
            
            self.assertEqual(prediction_response['status'], 'success')
            result = prediction_response['result']
            
            # Validate prediction format
            required_fields = ['symbol', 'action', 'confidence', 'timestamp']
            for field in required_fields:
                self.assertIn(field, result)
                
            self.assertEqual(result['symbol'], 'CBA.AX')
            self.assertIn(result['action'], ['BUY', 'SELL', 'HOLD', 'STRONG_BUY', 'STRONG_SELL'])
            self.assertGreaterEqual(result['confidence'], 0.0)
            self.assertLessEqual(result['confidence'], 1.0)
            
        asyncio.run(run_test())

class TestPaperTradingIntegration(unittest.TestCase):
    """Test paper trading integration with predictions"""
    
    def setUp(self):
        """Set up test harness"""
        self.harness = ServiceTestHarness()
        
    def tearDown(self):
        """Clean up test harness"""
        asyncio.run(self.harness.stop_all_services())
        
    @patch('redis.Redis')
    def test_paper_trading_prediction_integration(self, mock_redis):
        """Test paper trading service integration with prediction service"""
        mock_redis.from_url.return_value.ping.return_value = True
        
        async def run_test():
            from prediction_service import PredictionService
            from paper_trading_service import PaperTradingService
            
            # Start services
            prediction_service = await self.harness.start_test_service("prediction", PredictionService)
            trading_service = await self.harness.start_test_service("paper-trading", PaperTradingService)
            
            # Mock prediction in prediction service
            mock_prediction = {
                "symbol": "CBA.AX",
                "action": "BUY",
                "confidence": 0.85,
                "prediction_date": "2025-09-14",
                "timestamp": datetime.now().isoformat()
            }
            
            # Add mock method to prediction service
            async def mock_generate_prediction(symbol):
                return mock_prediction
                
            prediction_service.register_handler("generate_single_prediction", mock_generate_prediction)
            
            # Wait for services to initialize
            await asyncio.sleep(2)
            
            # Test prediction retrieval from trading service
            prediction_response = await self.harness.call_service("paper-trading", "get_prediction_for_symbol", symbol="CBA.AX")
            
            self.assertEqual(prediction_response['status'], 'success')
            
            # Test trade execution based on prediction
            trade_response = await self.harness.call_service("paper-trading", "execute_prediction_trade", symbol="CBA.AX", quantity=100)
            
            self.assertEqual(trade_response['status'], 'success')
            self.assertIn('trade_executed', trade_response['result'])
            
        asyncio.run(run_test())

class TestSchedulerIntegration(unittest.TestCase):
    """Test scheduler integration with other services"""
    
    def setUp(self):
        """Set up test harness"""
        self.harness = ServiceTestHarness()
        
    def tearDown(self):
        """Clean up test harness"""
        asyncio.run(self.harness.stop_all_services())
        
    @patch('redis.Redis')
    def test_scheduler_job_execution(self, mock_redis):
        """Test scheduler job execution calling other services"""
        mock_redis.from_url.return_value.ping.return_value = True
        
        async def run_test():
            from scheduler_service import SchedulerService
            from prediction_service import PredictionService
            
            # Start services
            await self.harness.start_test_service("prediction", PredictionService)
            scheduler_service = await self.harness.start_test_service("scheduler", SchedulerService)
            
            # Wait for services to initialize
            await asyncio.sleep(2)
            
            # Schedule a prediction job
            job_response = await self.harness.call_service("scheduler", "schedule_market_aware_job",
                job_id="test_prediction_job",
                job_type="prediction_generation",
                params={"symbols": ["CBA.AX", "ANZ.AX"]}
            )
            
            self.assertEqual(job_response['status'], 'success')
            
            # Execute the job
            execution_response = await self.harness.call_service("scheduler", "execute_job", job_id="test_prediction_job")
            
            self.assertEqual(execution_response['status'], 'success')
            
        asyncio.run(run_test())

class TestErrorPropagation(unittest.TestCase):
    """Test error propagation across services"""
    
    def setUp(self):
        """Set up test harness"""
        self.harness = ServiceTestHarness()
        
    def tearDown(self):
        """Clean up test harness"""
        asyncio.run(self.harness.stop_all_services())
        
    @patch('redis.Redis')
    def test_service_failure_handling(self, mock_redis):
        """Test handling of service failures in dependent services"""
        mock_redis.from_url.return_value.ping.return_value = True
        
        async def run_test():
            from prediction_service import PredictionService
            
            # Start only prediction service (without dependencies)
            prediction_service = await self.harness.start_test_service("prediction", PredictionService)
            
            # Wait for service to initialize
            await asyncio.sleep(2)
            
            # Try to generate prediction without market data service
            prediction_response = await self.harness.call_service("prediction", "generate_single_prediction", symbol="CBA.AX")
            
            # Should handle gracefully and either use fallback data or return appropriate error
            self.assertIn('status', prediction_response)
            
            if prediction_response['status'] == 'error':
                self.assertIn('error', prediction_response)
            else:
                # If it succeeds, it should be using fallback mechanisms
                self.assertEqual(prediction_response['status'], 'success')
                
        asyncio.run(run_test())

class TestDataFlow(unittest.TestCase):
    """Test data flow between services"""
    
    def setUp(self):
        """Set up test harness"""
        self.harness = ServiceTestHarness()
        
    def tearDown(self):
        """Clean up test harness"""
        asyncio.run(self.harness.stop_all_services())
        
    @patch('redis.Redis')
    def test_data_consistency_across_services(self, mock_redis):
        """Test data consistency when passed between services"""
        mock_redis.from_url.return_value.ping.return_value = True
        
        async def run_test():
            from market_data_service import MarketDataService
            from prediction_service import PredictionService
            
            # Start services
            await self.harness.start_test_service("market-data", MarketDataService)
            await self.harness.start_test_service("prediction", PredictionService)
            
            # Wait for services to initialize
            await asyncio.sleep(2)
            
            symbol = "CBA.AX"
            
            # Get market data directly
            market_response = await self.harness.call_service("market-data", "get_market_data", symbol=symbol)
            
            self.assertEqual(market_response['status'], 'success')
            market_data = market_response['result']
            
            # Generate prediction (which should use the same market data)
            prediction_response = await self.harness.call_service("prediction", "generate_single_prediction", symbol=symbol)
            
            self.assertEqual(prediction_response['status'], 'success')
            prediction_data = prediction_response['result']
            
            # Verify symbol consistency
            self.assertEqual(prediction_data['symbol'], symbol)
            
            # Verify data freshness (should be recent)
            prediction_time = datetime.fromisoformat(prediction_data['timestamp'].replace('Z', '+00:00'))
            time_diff = datetime.now() - prediction_time.replace(tzinfo=None)
            self.assertLess(time_diff.total_seconds(), 60)  # Within 1 minute
            
        asyncio.run(run_test())

class TestPerformanceIntegration(unittest.TestCase):
    """Test performance characteristics of integrated system"""
    
    def setUp(self):
        """Set up test harness"""
        self.harness = ServiceTestHarness()
        
    def tearDown(self):
        """Clean up test harness"""
        asyncio.run(self.harness.stop_all_services())
        
    @patch('redis.Redis')
    @patch('requests.get')
    def test_concurrent_service_calls(self, mock_get, mock_redis):
        """Test system performance under concurrent load"""
        mock_redis.from_url.return_value.ping.return_value = True
        
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Global Quote": {"05. price": "95.50", "06. volume": "1500000"}
        }
        mock_get.return_value = mock_response
        
        async def run_test():
            from prediction_service import PredictionService
            
            # Start prediction service
            await self.harness.start_test_service("prediction", PredictionService)
            
            # Wait for service to initialize
            await asyncio.sleep(2)
            
            # Execute concurrent predictions
            symbols = ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX", "MQG.AX"]
            
            start_time = time.time()
            
            # Create concurrent tasks
            tasks = []
            for symbol in symbols:
                task = asyncio.create_task(
                    self.harness.call_service("prediction", "generate_single_prediction", symbol=symbol)
                )
                tasks.append(task)
                
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Verify all predictions succeeded
            for result in results:
                self.assertEqual(result['status'], 'success')
                
            # Performance assertion - should complete within reasonable time
            self.assertLess(execution_time, 30.0)  # 30 seconds for 5 concurrent predictions
            
            # Calculate throughput
            predictions_per_second = len(symbols) / execution_time
            self.assertGreater(predictions_per_second, 0.2)  # At least 0.2 predictions/second
            
        asyncio.run(run_test())

def run_integration_tests():
    """Run all integration tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestServiceCommunication,
        TestPredictionWorkflow,
        TestPaperTradingIntegration,
        TestSchedulerIntegration,
        TestErrorPropagation,
        TestDataFlow,
        TestPerformanceIntegration
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
        
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result

if __name__ == "__main__":
    result = run_integration_tests()
    
    # Exit with appropriate code
    if result.failures or result.errors:
        print(f"\n❌ Integration tests failed: {len(result.failures)} failures, {len(result.errors)} errors")
        sys.exit(1)
    else:
        print("\n✅ All integration tests passed!")
        sys.exit(0)
