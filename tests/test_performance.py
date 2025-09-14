#!/usr/bin/env python3
"""
Performance Tests for Trading Microservices

This module contains comprehensive performance tests for the trading microservices,
including load testing, stress testing, memory profiling, and latency analysis.

Author: Trading System Testing Team
Date: September 14, 2025
"""

import unittest
import asyncio
import time
import statistics
import psutil
import threading
import concurrent.futures
import json
import os
import sys
import tempfile
import gc
import tracemalloc
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add services to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services'))

class PerformanceProfiler:
    """Performance profiling utilities"""
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
        
    def start_timer(self, name: str):
        """Start timing an operation"""
        self.start_times[name] = time.perf_counter()
        
    def stop_timer(self, name: str):
        """Stop timing and record duration"""
        if name in self.start_times:
            duration = time.perf_counter() - self.start_times[name]
            if name not in self.metrics:
                self.metrics[name] = []
            self.metrics[name].append(duration)
            del self.start_times[name]
            return duration
        return None
        
    def get_stats(self, name: str):
        """Get statistics for a metric"""
        if name not in self.metrics or not self.metrics[name]:
            return None
            
        data = self.metrics[name]
        return {
            'count': len(data),
            'mean': statistics.mean(data),
            'median': statistics.median(data),
            'min': min(data),
            'max': max(data),
            'std_dev': statistics.stdev(data) if len(data) > 1 else 0,
            'p95': self._percentile(data, 95),
            'p99': self._percentile(data, 99)
        }
        
    def _percentile(self, data, percentile):
        """Calculate percentile"""
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))

class MemoryProfiler:
    """Memory profiling utilities"""
    
    def __init__(self):
        self.baseline_memory = None
        self.peak_memory = None
        self.snapshots = []
        
    def start_monitoring(self):
        """Start memory monitoring"""
        tracemalloc.start()
        self.baseline_memory = self._get_memory_usage()
        self.peak_memory = self.baseline_memory
        
    def stop_monitoring(self):
        """Stop memory monitoring"""
        tracemalloc.stop()
        
    def take_snapshot(self, label: str = None):
        """Take a memory snapshot"""
        current_memory = self._get_memory_usage()
        
        if current_memory > self.peak_memory:
            self.peak_memory = current_memory
            
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'memory_mb': current_memory,
            'label': label
        }
        
        self.snapshots.append(snapshot)
        return snapshot
        
    def _get_memory_usage(self):
        """Get current memory usage in MB"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
        
    def get_memory_delta(self):
        """Get memory delta from baseline"""
        if self.baseline_memory is None:
            return None
        return self._get_memory_usage() - self.baseline_memory

class TestServicePerformance(unittest.TestCase):
    """Test individual service performance"""
    
    def setUp(self):
        """Set up performance testing"""
        self.profiler = PerformanceProfiler()
        self.memory_profiler = MemoryProfiler()
        
    def test_base_service_response_time(self):
        """Test BaseService response times"""
        from base_service import BaseService
        
        async def run_test():
            with patch('redis.Redis') as mock_redis:
                mock_redis.from_url.return_value.ping.return_value = True
                
                service = BaseService("perf-test")
                
                # Test health check response times
                for i in range(100):
                    self.profiler.start_timer('health_check')
                    result = await service.health_check()
                    self.profiler.stop_timer('health_check')
                    
                    self.assertIsNotNone(result)
                    
                stats = self.profiler.get_stats('health_check')
                
                # Performance assertions
                self.assertLess(stats['mean'], 0.001)  # < 1ms mean
                self.assertLess(stats['p95'], 0.005)   # < 5ms P95
                self.assertLess(stats['max'], 0.010)   # < 10ms max
                
        asyncio.run(run_test())
        
    def test_prediction_service_throughput(self):
        """Test prediction service throughput"""
        from prediction_service import PredictionService
        
        async def run_test():
            with patch('redis.Redis') as mock_redis:
                mock_redis.from_url.return_value.ping.return_value = True
                
                service = PredictionService()
                
                # Mock the predictor
                mock_prediction = {
                    "symbol": "TEST.AX",
                    "action": "BUY",
                    "confidence": 0.75,
                    "timestamp": datetime.now().isoformat()
                }
                
                service.predictor.calculate_confidence = Mock(return_value=mock_prediction)
                
                # Test prediction generation throughput
                symbols = ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX", "MQG.AX"] * 10  # 50 predictions
                
                start_time = time.perf_counter()
                
                for symbol in symbols:
                    self.profiler.start_timer('prediction_generation')
                    result = await service._generate_fresh_prediction(symbol)
                    self.profiler.stop_timer('prediction_generation')
                    
                    self.assertIsNotNone(result)
                    
                end_time = time.perf_counter()
                total_time = end_time - start_time
                
                # Throughput calculation
                throughput = len(symbols) / total_time
                
                stats = self.profiler.get_stats('prediction_generation')
                
                # Performance assertions
                self.assertGreater(throughput, 5)      # > 5 predictions/second
                self.assertLess(stats['mean'], 0.2)    # < 200ms mean
                self.assertLess(stats['p95'], 0.5)     # < 500ms P95
                
        asyncio.run(run_test())

class TestConcurrentLoad(unittest.TestCase):
    """Test system behavior under concurrent load"""
    
    def setUp(self):
        """Set up load testing"""
        self.profiler = PerformanceProfiler()
        self.memory_profiler = MemoryProfiler()
        
    def test_concurrent_service_calls(self):
        """Test concurrent calls to single service"""
        from base_service import BaseService
        
        async def run_test():
            with patch('redis.Redis') as mock_redis:
                mock_redis.from_url.return_value.ping.return_value = True
                
                service = BaseService("load-test")
                
                # Concurrent health checks
                concurrent_requests = 50
                
                async def make_request():
                    self.profiler.start_timer('concurrent_health')
                    result = await service.health_check()
                    self.profiler.stop_timer('concurrent_health')
                    return result
                    
                # Execute concurrent requests
                start_time = time.perf_counter()
                
                tasks = [make_request() for _ in range(concurrent_requests)]
                results = await asyncio.gather(*tasks)
                
                end_time = time.perf_counter()
                total_time = end_time - start_time
                
                # Verify all requests succeeded
                self.assertEqual(len(results), concurrent_requests)
                for result in results:
                    self.assertIsNotNone(result)
                    
                stats = self.profiler.get_stats('concurrent_health')
                
                # Performance assertions
                throughput = concurrent_requests / total_time
                self.assertGreater(throughput, 100)    # > 100 requests/second
                self.assertLess(stats['p95'], 0.1)     # < 100ms P95
                
        asyncio.run(run_test())
        
    def test_memory_usage_under_load(self):
        """Test memory usage under sustained load"""
        from prediction_service import PredictionService
        
        async def run_test():
            with patch('redis.Redis') as mock_redis:
                mock_redis.from_url.return_value.ping.return_value = True
                
                self.memory_profiler.start_monitoring()
                
                service = PredictionService()
                
                # Mock predictor
                mock_prediction = {
                    "symbol": "TEST.AX",
                    "action": "BUY", 
                    "confidence": 0.75,
                    "timestamp": datetime.now().isoformat()
                }
                
                service.predictor.calculate_confidence = Mock(return_value=mock_prediction)
                
                self.memory_profiler.take_snapshot("baseline")
                
                # Generate predictions in batches
                for batch in range(10):
                    symbols = ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX", "MQG.AX"]
                    
                    for symbol in symbols:
                        await service._generate_fresh_prediction(symbol)
                        
                    # Force garbage collection
                    gc.collect()
                    
                    self.memory_profiler.take_snapshot(f"batch_{batch}")
                    
                # Check memory growth
                memory_delta = self.memory_profiler.get_memory_delta()
                
                # Memory assertions - should not grow excessively
                self.assertLess(memory_delta, 50)  # < 50MB growth
                
                self.memory_profiler.stop_monitoring()
                
        asyncio.run(run_test())

class TestStressConditions(unittest.TestCase):
    """Test system behavior under stress conditions"""
    
    def setUp(self):
        """Set up stress testing"""
        self.profiler = PerformanceProfiler()
        
    def test_high_frequency_requests(self):
        """Test behavior with very high frequency requests"""
        from base_service import BaseService
        
        async def run_test():
            with patch('redis.Redis') as mock_redis:
                mock_redis.from_url.return_value.ping.return_value = True
                
                service = BaseService("stress-test")
                
                # High frequency requests (1000 requests in rapid succession)
                request_count = 1000
                success_count = 0
                error_count = 0
                
                start_time = time.perf_counter()
                
                for i in range(request_count):
                    try:
                        self.profiler.start_timer('stress_request')
                        result = await service.health_check()
                        self.profiler.stop_timer('stress_request')
                        
                        if result:
                            success_count += 1
                        else:
                            error_count += 1
                            
                    except Exception:
                        error_count += 1
                        
                end_time = time.perf_counter()
                total_time = end_time - start_time
                
                # Calculate metrics
                success_rate = success_count / request_count
                throughput = request_count / total_time
                
                stats = self.profiler.get_stats('stress_request')
                
                # Stress test assertions
                self.assertGreater(success_rate, 0.95)  # > 95% success rate
                self.assertGreater(throughput, 50)      # > 50 requests/second
                
                if stats:
                    self.assertLess(stats['p99'], 1.0)  # < 1s P99 even under stress
                    
        asyncio.run(run_test())
        
    def test_resource_exhaustion_handling(self):
        """Test handling of resource exhaustion"""
        from prediction_service import PredictionService
        
        async def run_test():
            with patch('redis.Redis') as mock_redis:
                mock_redis.from_url.return_value.ping.return_value = True
                
                service = PredictionService()
                
                # Mock predictor to use more memory
                def memory_intensive_prediction(*args, **kwargs):
                    # Create large temporary data structures
                    large_data = ['x' * 1024] * 1000  # 1MB of data
                    
                    return {
                        "symbol": "TEST.AX",
                        "action": "BUY",
                        "confidence": 0.75,
                        "timestamp": datetime.now().isoformat(),
                        "large_data": large_data  # This will be cleaned up
                    }
                    
                service.predictor.calculate_confidence = Mock(side_effect=memory_intensive_prediction)
                
                # Generate many predictions to test memory handling
                symbols = ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX", "MQG.AX"] * 20  # 100 predictions
                
                success_count = 0
                error_count = 0
                
                for symbol in symbols:
                    try:
                        result = await service._generate_fresh_prediction(symbol)
                        if result:
                            success_count += 1
                        else:
                            error_count += 1
                            
                        # Occasional garbage collection
                        if success_count % 10 == 0:
                            gc.collect()
                            
                    except Exception:
                        error_count += 1
                        
                # Resource handling assertions
                total_requests = success_count + error_count
                success_rate = success_count / total_requests if total_requests > 0 else 0
                
                # Should handle at least 80% successfully even under memory pressure
                self.assertGreater(success_rate, 0.8)
                
        asyncio.run(run_test())

class TestLatencyAnalysis(unittest.TestCase):
    """Test system latency characteristics"""
    
    def setUp(self):
        """Set up latency testing"""
        self.profiler = PerformanceProfiler()
        
    def test_cold_start_latency(self):
        """Test cold start performance"""
        from prediction_service import PredictionService
        
        async def run_test():
            with patch('redis.Redis') as mock_redis:
                mock_redis.from_url.return_value.ping.return_value = True
                
                # Test service initialization time
                self.profiler.start_timer('service_init')
                service = PredictionService()
                self.profiler.stop_timer('service_init')
                
                # Mock predictor
                service.predictor.calculate_confidence = Mock(return_value={
                    "symbol": "TEST.AX",
                    "action": "BUY",
                    "confidence": 0.75,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Test first prediction (cold start)
                self.profiler.start_timer('cold_start_prediction')
                first_result = await service._generate_fresh_prediction("CBA.AX")
                self.profiler.stop_timer('cold_start_prediction')
                
                # Test subsequent predictions (warm)
                for i in range(10):
                    self.profiler.start_timer('warm_prediction')
                    result = await service._generate_fresh_prediction("ANZ.AX")
                    self.profiler.stop_timer('warm_prediction')
                    
                # Analyze latency characteristics
                init_stats = self.profiler.get_stats('service_init')
                cold_stats = self.profiler.get_stats('cold_start_prediction')
                warm_stats = self.profiler.get_stats('warm_prediction')
                
                # Latency assertions
                self.assertIsNotNone(init_stats)
                self.assertLess(init_stats['mean'], 1.0)     # < 1s initialization
                
                self.assertIsNotNone(cold_stats)
                self.assertLess(cold_stats['mean'], 2.0)     # < 2s cold start
                
                self.assertIsNotNone(warm_stats)
                self.assertLess(warm_stats['mean'], 0.1)     # < 100ms warm
                
                # Warm should be significantly faster than cold
                if cold_stats and warm_stats:
                    self.assertLess(warm_stats['mean'], cold_stats['mean'] / 2)
                    
        asyncio.run(run_test())

class TestScalabilityLimits(unittest.TestCase):
    """Test system scalability limits"""
    
    def setUp(self):
        """Set up scalability testing"""
        self.profiler = PerformanceProfiler()
        
    def test_connection_limits(self):
        """Test Unix socket connection limits"""
        from base_service import BaseService
        
        async def run_test():
            with patch('redis.Redis') as mock_redis:
                mock_redis.from_url.return_value.ping.return_value = True
                
                service = BaseService("scale-test")
                
                # Test maximum concurrent connections
                max_connections = 100
                
                async def make_connection():
                    try:
                        self.profiler.start_timer('connection_time')
                        result = await service.health_check()
                        self.profiler.stop_timer('connection_time')
                        return result is not None
                    except Exception:
                        return False
                        
                # Create many concurrent connections
                tasks = [make_connection() for _ in range(max_connections)]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Count successful connections
                successful = sum(1 for r in results if r is True)
                
                stats = self.profiler.get_stats('connection_time')
                
                # Scalability assertions
                success_rate = successful / max_connections
                self.assertGreater(success_rate, 0.9)  # > 90% success rate
                
                if stats:
                    self.assertLess(stats['p95'], 1.0)  # < 1s P95 even with many connections
                    
        asyncio.run(run_test())

def run_performance_tests():
    """Run all performance tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestServicePerformance,
        TestConcurrentLoad,
        TestStressConditions,
        TestLatencyAnalysis,
        TestScalabilityLimits
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
        
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    return result

if __name__ == "__main__":
    print("🚀 Starting Performance Tests for Trading Microservices...")
    print("=" * 80)
    
    # Check system resources
    memory = psutil.virtual_memory()
    cpu_count = psutil.cpu_count()
    
    print(f"System Info:")
    print(f"  Total Memory: {memory.total / 1024 / 1024 / 1024:.1f} GB")
    print(f"  Available Memory: {memory.available / 1024 / 1024 / 1024:.1f} GB")
    print(f"  CPU Cores: {cpu_count}")
    print("=" * 80)
    
    result = run_performance_tests()
    
    print("\n" + "=" * 80)
    print("PERFORMANCE TEST SUMMARY")
    print("=" * 80)
    
    if result.failures or result.errors:
        print(f"❌ Performance tests failed:")
        print(f"   Failures: {len(result.failures)}")
        print(f"   Errors: {len(result.errors)}")
        
        if result.failures:
            print("\nFailure Details:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
                
        sys.exit(1)
    else:
        print("✅ All performance tests passed!")
        print(f"   Total tests run: {result.testsRun}")
        print(f"   Execution time: {result.testsRun} tests completed")
        
    print("=" * 80)
    sys.exit(0)
