#!/usr/bin/env python3
"""
Performance Analysis Service
Comprehensive performance testing and optimization for all trading microservices
Monitors resource usage, response times, and system efficiency

Key Features:
- Real-time performance monitoring across all services
- Resource usage analysis (CPU, memory, disk I/O)
- Response time benchmarking and SLA validation
- Bottleneck identification and optimization recommendations
- Load testing and stress testing capabilities
- Performance regression detection

Dependencies:
- All trading microservices for performance testing
- System monitoring tools (psutil)
- Performance benchmarking frameworks

Related Files:
- services/base/base_service.py (base performance metrics)
- All service implementations for performance validation
"""

import asyncio
import sys
import os
import json
import time
import psutil
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import statistics
import traceback
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import threading

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.base_service import BaseService

# Settings.py integration for performance configuration
SETTINGS_AVAILABLE = False
try:
    sys.path.append("app/config")
    import settings as Settings
    SETTINGS_AVAILABLE = True
except ImportError:
    try:
        sys.path.append("paper-trading-app/app/config")
        import settings as Settings
        SETTINGS_AVAILABLE = True
    except ImportError:
        Settings = None
        print("Warning: settings.py not found - using fallback performance configuration")

@dataclass
class PerformanceMetrics:
    """Performance metrics for a service or operation"""
    service_name: str
    operation: str
    response_time_ms: float
    cpu_usage_percent: float
    memory_usage_mb: float
    disk_io_mb: float
    network_io_mb: float
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result

@dataclass
class LoadTestResult:
    """Results from load testing"""
    service_name: str
    concurrent_requests: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    min_response_time: float
    max_response_time: float
    percentile_95: float
    percentile_99: float
    requests_per_second: float
    test_duration_seconds: float
    errors: List[str]

class PerformanceAnalysisService(BaseService):
    """
    Comprehensive performance analysis service for trading microservices
    Monitors and optimizes system performance across all components
    """
    
    def __init__(self):
        super().__init__("performance-analysis")
        
        # Performance configuration
        self.performance_config = self._load_performance_config()
        
        # Services to monitor
        self.monitored_services = [
            "market-data",
            "sentiment", 
            "prediction",
            "paper-trading",
            "ml-model",
            "scheduler",
            "database",
            "api-consistency",
            "error-handling",
            "security-validation"
        ]
        
        # Performance data storage
        self.performance_history: List[PerformanceMetrics] = []
        self.load_test_results: Dict[str, List[LoadTestResult]] = {}
        self.baseline_metrics: Dict[str, PerformanceMetrics] = {}
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_task = None
        
        # Performance thresholds (from settings or defaults)
        self.performance_thresholds = self.performance_config.get('thresholds', {
            'response_time_ms': 5000,  # 5 seconds max
            'cpu_usage_percent': 80,   # 80% max CPU
            'memory_usage_mb': 512,    # 512MB max memory per service
            'requests_per_second': 10  # Minimum RPS capability
        })
        
        # Register performance analysis methods
        self.register_handler("start_monitoring", self.start_monitoring)
        self.register_handler("stop_monitoring", self.stop_monitoring)
        self.register_handler("get_performance_metrics", self.get_performance_metrics)
        self.register_handler("run_load_test", self.run_load_test)
        self.register_handler("benchmark_service", self.benchmark_service)
        self.register_handler("analyze_bottlenecks", self.analyze_bottlenecks)
        self.register_handler("get_performance_report", self.get_performance_report)
        self.register_handler("optimize_recommendations", self.optimize_recommendations)
        self.register_handler("stress_test", self.stress_test)
        self.register_handler("validate_sla", self.validate_sla)
        
    def _load_performance_config(self) -> Dict[str, Any]:
        """Load performance configuration from settings"""
        if SETTINGS_AVAILABLE and hasattr(Settings, 'PERFORMANCE_CONFIG'):
            return Settings.PERFORMANCE_CONFIG
        else:
            # Fallback performance configuration
            return {
                'monitoring_interval': 30,  # seconds
                'retention_days': 7,
                'thresholds': {
                    'response_time_ms': 5000,
                    'cpu_usage_percent': 80,
                    'memory_usage_mb': 512,
                    'requests_per_second': 10
                },
                'load_test': {
                    'default_concurrent_users': 10,
                    'default_duration': 60,
                    'ramp_up_time': 10
                },
                'alerts': {
                    'enabled': True,
                    'performance_degradation_threshold': 50  # 50% performance drop
                }
            }
    
    async def start_monitoring(self, interval_seconds: int = None) -> Dict[str, Any]:
        """Start continuous performance monitoring"""
        if self.monitoring_active:
            return {"status": "already_running", "message": "Performance monitoring is already active"}
        
        interval = interval_seconds or self.performance_config.get('monitoring_interval', 30)
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop(interval))
        
        self.logger.info(f'"interval": {interval}, "action": "performance_monitoring_started"')
        
        return {
            "status": "started",
            "monitoring_interval": interval,
            "monitored_services": len(self.monitored_services)
        }
    
    async def stop_monitoring(self) -> Dict[str, Any]:
        """Stop continuous performance monitoring"""
        if not self.monitoring_active:
            return {"status": "not_running", "message": "Performance monitoring is not active"}
        
        self.monitoring_active = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info('"action": "performance_monitoring_stopped"')
        
        return {
            "status": "stopped",
            "metrics_collected": len(self.performance_history)
        }
    
    async def _monitoring_loop(self, interval: int):
        """Continuous monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect metrics from all services
                await self._collect_system_metrics()
                
                # Check for performance alerts
                await self._check_performance_alerts()
                
                # Cleanup old metrics
                self._cleanup_old_metrics()
                
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f'"error": "{e}", "action": "monitoring_loop_error"')
                await asyncio.sleep(interval)
    
    async def _collect_system_metrics(self):
        """Collect performance metrics from all services"""
        for service_name in self.monitored_services:
            try:
                metrics = await self._collect_service_metrics(service_name)
                if metrics:
                    self.performance_history.append(metrics)
                    
            except Exception as e:
                # Record failed metric collection
                error_metrics = PerformanceMetrics(
                    service_name=service_name,
                    operation="health_check",
                    response_time_ms=0,
                    cpu_usage_percent=0,
                    memory_usage_mb=0,
                    disk_io_mb=0,
                    network_io_mb=0,
                    timestamp=datetime.now(),
                    success=False,
                    error_message=str(e)
                )
                self.performance_history.append(error_metrics)
    
    async def _collect_service_metrics(self, service_name: str) -> Optional[PerformanceMetrics]:
        """Collect performance metrics for a specific service"""
        start_time = time.time()
        
        try:
            # Get system metrics before call
            process = psutil.Process()
            cpu_before = process.cpu_percent()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            # Call service health endpoint
            health_result = await self.call_service(service_name, "health", timeout=10.0)
            
            # Calculate response time
            response_time = (time.time() - start_time) * 1000  # milliseconds
            
            # Get system metrics after call
            cpu_after = process.cpu_percent()
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            
            # Estimate resource usage (simplified)
            cpu_usage = max(cpu_after - cpu_before, 0)
            memory_usage = memory_after
            
            # Get service-specific metrics if available
            service_memory = 0
            service_cpu = 0
            
            if isinstance(health_result, dict):
                service_memory = health_result.get('memory_usage', 0) / 1024 / 1024  # Convert to MB
                service_cpu = health_result.get('cpu_usage', 0)
            
            return PerformanceMetrics(
                service_name=service_name,
                operation="health_check",
                response_time_ms=response_time,
                cpu_usage_percent=service_cpu or cpu_usage,
                memory_usage_mb=service_memory or memory_usage,
                disk_io_mb=0,  # TODO: Implement disk I/O monitoring
                network_io_mb=0,  # TODO: Implement network I/O monitoring
                timestamp=datetime.now(),
                success=True
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            return PerformanceMetrics(
                service_name=service_name,
                operation="health_check",
                response_time_ms=response_time,
                cpu_usage_percent=0,
                memory_usage_mb=0,
                disk_io_mb=0,
                network_io_mb=0,
                timestamp=datetime.now(),
                success=False,
                error_message=str(e)
            )
    
    async def _check_performance_alerts(self):
        """Check for performance threshold violations"""
        if not self.performance_config.get('alerts', {}).get('enabled', True):
            return
        
        recent_metrics = [m for m in self.performance_history 
                         if (datetime.now() - m.timestamp).seconds < 300]  # Last 5 minutes
        
        for service_name in self.monitored_services:
            service_metrics = [m for m in recent_metrics if m.service_name == service_name and m.success]
            
            if not service_metrics:
                continue
            
            # Check average response time
            avg_response_time = statistics.mean([m.response_time_ms for m in service_metrics])
            if avg_response_time > self.performance_thresholds['response_time_ms']:
                self.publish_event("performance_alert", {
                    "alert_type": "high_response_time",
                    "service": service_name,
                    "value": avg_response_time,
                    "threshold": self.performance_thresholds['response_time_ms'],
                    "timestamp": datetime.now().isoformat()
                }, priority="high")
            
            # Check memory usage
            avg_memory = statistics.mean([m.memory_usage_mb for m in service_metrics])
            if avg_memory > self.performance_thresholds['memory_usage_mb']:
                self.publish_event("performance_alert", {
                    "alert_type": "high_memory_usage",
                    "service": service_name,
                    "value": avg_memory,
                    "threshold": self.performance_thresholds['memory_usage_mb'],
                    "timestamp": datetime.now().isoformat()
                }, priority="high")
    
    def _cleanup_old_metrics(self):
        """Remove old performance metrics to prevent memory growth"""
        retention_days = self.performance_config.get('retention_days', 7)
        cutoff_time = datetime.now() - timedelta(days=retention_days)
        
        self.performance_history = [
            m for m in self.performance_history 
            if m.timestamp > cutoff_time
        ]
    
    async def get_performance_metrics(self, service_name: str = None, 
                                    hours: int = 24) -> Dict[str, Any]:
        """Get performance metrics for analysis"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        if service_name:
            filtered_metrics = [
                m for m in self.performance_history 
                if m.service_name == service_name and m.timestamp > cutoff_time
            ]
        else:
            filtered_metrics = [
                m for m in self.performance_history 
                if m.timestamp > cutoff_time
            ]
        
        if not filtered_metrics:
            return {
                "service": service_name or "all",
                "period_hours": hours,
                "metrics_found": 0,
                "message": "No metrics found for specified period"
            }
        
        # Calculate statistics
        successful_metrics = [m for m in filtered_metrics if m.success]
        
        stats = {
            "service": service_name or "all",
            "period_hours": hours,
            "total_measurements": len(filtered_metrics),
            "successful_measurements": len(successful_metrics),
            "success_rate": len(successful_metrics) / len(filtered_metrics) * 100,
            "response_times": {},
            "resource_usage": {},
            "errors": [m.error_message for m in filtered_metrics if not m.success and m.error_message]
        }
        
        if successful_metrics:
            response_times = [m.response_time_ms for m in successful_metrics]
            cpu_usage = [m.cpu_usage_percent for m in successful_metrics]
            memory_usage = [m.memory_usage_mb for m in successful_metrics]
            
            stats["response_times"] = {
                "average": statistics.mean(response_times),
                "median": statistics.median(response_times),
                "min": min(response_times),
                "max": max(response_times),
                "p95": self._percentile(response_times, 95),
                "p99": self._percentile(response_times, 99)
            }
            
            stats["resource_usage"] = {
                "cpu": {
                    "average": statistics.mean(cpu_usage),
                    "max": max(cpu_usage)
                },
                "memory": {
                    "average": statistics.mean(memory_usage),
                    "max": max(memory_usage)
                }
            }
        
        return stats
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    async def run_load_test(self, service_name: str, endpoint: str = "health",
                          concurrent_users: int = None, duration_seconds: int = None,
                          **params) -> LoadTestResult:
        """Run load test against a service"""
        concurrent_users = concurrent_users or self.performance_config.get('load_test', {}).get('default_concurrent_users', 10)
        duration_seconds = duration_seconds or self.performance_config.get('load_test', {}).get('default_duration', 60)
        
        self.logger.info(f'"service": "{service_name}", "endpoint": "{endpoint}", "concurrent_users": {concurrent_users}, "duration": {duration_seconds}, "action": "load_test_started"')
        
        # Prepare test
        results = []
        errors = []
        start_time = time.time()
        
        async def make_request():
            """Individual request for load testing"""
            request_start = time.time()
            try:
                await self.call_service(service_name, endpoint, timeout=30.0, **params)
                request_time = (time.time() - request_start) * 1000
                return {"success": True, "response_time": request_time}
            except Exception as e:
                request_time = (time.time() - request_start) * 1000
                return {"success": False, "response_time": request_time, "error": str(e)}
        
        # Run load test
        tasks = []
        end_time = start_time + duration_seconds
        
        while time.time() < end_time:
            # Launch concurrent requests
            batch_tasks = [
                asyncio.create_task(make_request()) 
                for _ in range(concurrent_users)
            ]
            
            # Wait for batch completion
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, dict):
                    results.append(result)
                    if not result["success"]:
                        errors.append(result.get("error", "Unknown error"))
                else:
                    errors.append(str(result))
            
            # Brief pause between batches
            await asyncio.sleep(0.1)
        
        # Calculate results
        test_duration = time.time() - start_time
        successful_requests = len([r for r in results if r.get("success", False)])
        failed_requests = len(results) - successful_requests
        
        response_times = [r["response_time"] for r in results if r.get("success", False)]
        
        load_test_result = LoadTestResult(
            service_name=service_name,
            concurrent_requests=concurrent_users,
            total_requests=len(results),
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=statistics.mean(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            percentile_95=self._percentile(response_times, 95) if response_times else 0,
            percentile_99=self._percentile(response_times, 99) if response_times else 0,
            requests_per_second=len(results) / test_duration if test_duration > 0 else 0,
            test_duration_seconds=test_duration,
            errors=errors[:10]  # Limit error list
        )
        
        # Store results
        if service_name not in self.load_test_results:
            self.load_test_results[service_name] = []
        self.load_test_results[service_name].append(load_test_result)
        
        self.logger.info(f'"service": "{service_name}", "total_requests": {len(results)}, "success_rate": {successful_requests/len(results)*100:.1f}, "avg_response_time": {load_test_result.average_response_time:.1f}, "action": "load_test_completed"')
        
        return load_test_result
    
    async def benchmark_service(self, service_name: str) -> Dict[str, Any]:
        """Run comprehensive benchmark for a service"""
        benchmark_result = {
            "service": service_name,
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
        
        # Test 1: Basic health check performance
        health_test = await self._benchmark_operation(service_name, "health", iterations=50)
        benchmark_result["tests"]["health_check"] = health_test
        
        # Test 2: Load test
        load_test = await self.run_load_test(service_name, concurrent_users=5, duration_seconds=30)
        benchmark_result["tests"]["load_test"] = asdict(load_test)
        
        # Test 3: Service-specific operations
        if service_name == "prediction":
            prediction_test = await self._benchmark_operation(
                service_name, "generate_single_prediction", 
                iterations=10, symbol="CBA.AX"
            )
            benchmark_result["tests"]["prediction_operation"] = prediction_test
        
        elif service_name == "market-data":
            market_test = await self._benchmark_operation(
                service_name, "get_market_data",
                iterations=10, symbol="CBA.AX"
            )
            benchmark_result["tests"]["market_data_operation"] = market_test
        
        # Calculate overall performance score
        performance_score = self._calculate_performance_score(benchmark_result)
        benchmark_result["performance_score"] = performance_score
        
        return benchmark_result
    
    async def _benchmark_operation(self, service_name: str, operation: str, 
                                 iterations: int = 10, **params) -> Dict[str, Any]:
        """Benchmark a specific operation"""
        results = []
        
        for i in range(iterations):
            start_time = time.time()
            try:
                await self.call_service(service_name, operation, timeout=30.0, **params)
                response_time = (time.time() - start_time) * 1000
                results.append({"success": True, "response_time": response_time})
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                results.append({"success": False, "response_time": response_time, "error": str(e)})
        
        successful_results = [r for r in results if r["success"]]
        response_times = [r["response_time"] for r in successful_results]
        
        return {
            "operation": operation,
            "iterations": iterations,
            "success_rate": len(successful_results) / iterations * 100,
            "response_times": {
                "average": statistics.mean(response_times) if response_times else 0,
                "min": min(response_times) if response_times else 0,
                "max": max(response_times) if response_times else 0,
                "median": statistics.median(response_times) if response_times else 0
            },
            "errors": [r.get("error") for r in results if not r["success"]]
        }
    
    def _calculate_performance_score(self, benchmark_result: Dict[str, Any]) -> float:
        """Calculate overall performance score (0-100)"""
        score = 100.0
        
        for test_name, test_result in benchmark_result["tests"].items():
            if test_name == "load_test":
                # Penalize high response times and low success rates
                avg_response = test_result.get("average_response_time", 0)
                success_rate = test_result.get("successful_requests", 0) / max(test_result.get("total_requests", 1), 1) * 100
                
                if avg_response > 1000:  # > 1 second
                    score -= 20
                elif avg_response > 500:  # > 500ms
                    score -= 10
                
                if success_rate < 95:
                    score -= 15
                
            else:
                # Regular operation tests
                success_rate = test_result.get("success_rate", 0)
                avg_response = test_result.get("response_times", {}).get("average", 0)
                
                if success_rate < 90:
                    score -= 10
                
                if avg_response > 2000:  # > 2 seconds
                    score -= 10
                elif avg_response > 1000:  # > 1 second
                    score -= 5
        
        return max(0, min(100, score))
    
    async def analyze_bottlenecks(self, service_name: str = None) -> Dict[str, Any]:
        """Analyze performance bottlenecks"""
        analysis_result = {
            "timestamp": datetime.now().isoformat(),
            "bottlenecks_identified": [],
            "recommendations": []
        }
        
        services_to_analyze = [service_name] if service_name else self.monitored_services
        
        for service in services_to_analyze:
            recent_metrics = [
                m for m in self.performance_history 
                if m.service_name == service and 
                (datetime.now() - m.timestamp).seconds < 3600  # Last hour
            ]
            
            if not recent_metrics:
                continue
            
            successful_metrics = [m for m in recent_metrics if m.success]
            
            if not successful_metrics:
                analysis_result["bottlenecks_identified"].append({
                    "service": service,
                    "type": "availability_issue",
                    "description": "Service not responding successfully",
                    "severity": "critical"
                })
                continue
            
            # Analyze response times
            response_times = [m.response_time_ms for m in successful_metrics]
            avg_response = statistics.mean(response_times)
            
            if avg_response > self.performance_thresholds['response_time_ms']:
                analysis_result["bottlenecks_identified"].append({
                    "service": service,
                    "type": "slow_response",
                    "description": f"Average response time {avg_response:.1f}ms exceeds threshold",
                    "severity": "high" if avg_response > self.performance_thresholds['response_time_ms'] * 2 else "medium"
                })
            
            # Analyze memory usage
            memory_usage = [m.memory_usage_mb for m in successful_metrics]
            avg_memory = statistics.mean(memory_usage)
            
            if avg_memory > self.performance_thresholds['memory_usage_mb']:
                analysis_result["bottlenecks_identified"].append({
                    "service": service,
                    "type": "high_memory_usage",
                    "description": f"Average memory usage {avg_memory:.1f}MB exceeds threshold",
                    "severity": "medium"
                })
            
            # Analyze CPU usage
            cpu_usage = [m.cpu_usage_percent for m in successful_metrics]
            avg_cpu = statistics.mean(cpu_usage)
            
            if avg_cpu > self.performance_thresholds['cpu_usage_percent']:
                analysis_result["bottlenecks_identified"].append({
                    "service": service,
                    "type": "high_cpu_usage",
                    "description": f"Average CPU usage {avg_cpu:.1f}% exceeds threshold",
                    "severity": "medium"
                })
        
        # Generate recommendations
        if analysis_result["bottlenecks_identified"]:
            analysis_result["recommendations"] = self._generate_optimization_recommendations(
                analysis_result["bottlenecks_identified"]
            )
        else:
            analysis_result["recommendations"] = ["No significant performance bottlenecks identified"]
        
        return analysis_result
    
    def _generate_optimization_recommendations(self, bottlenecks: List[Dict]) -> List[str]:
        """Generate optimization recommendations based on bottlenecks"""
        recommendations = []
        
        bottleneck_types = [b["type"] for b in bottlenecks]
        
        if "slow_response" in bottleneck_types:
            recommendations.append("Consider optimizing database queries and caching frequently accessed data")
            recommendations.append("Review algorithm efficiency in prediction and analysis services")
        
        if "high_memory_usage" in bottleneck_types:
            recommendations.append("Implement memory pooling and object reuse patterns")
            recommendations.append("Review data structures for memory efficiency")
        
        if "high_cpu_usage" in bottleneck_types:
            recommendations.append("Consider implementing request queuing and rate limiting")
            recommendations.append("Optimize computational algorithms and consider parallel processing")
        
        if "availability_issue" in bottleneck_types:
            recommendations.append("Implement health checks and automatic service recovery")
            recommendations.append("Review error handling and failover mechanisms")
        
        # General recommendations
        recommendations.append("Monitor performance trends and set up automated alerting")
        recommendations.append("Consider horizontal scaling for high-load services")
        
        return recommendations
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        report = {
            "report_timestamp": datetime.now().isoformat(),
            "monitoring_status": "active" if self.monitoring_active else "inactive",
            "metrics_collected": len(self.performance_history),
            "services_monitored": len(self.monitored_services),
            "service_performance": {},
            "system_health": "good",
            "critical_issues": [],
            "recommendations": []
        }
        
        # Get performance metrics for each service
        for service_name in self.monitored_services:
            service_metrics = await self.get_performance_metrics(service_name, hours=24)
            report["service_performance"][service_name] = service_metrics
            
            # Check for critical issues
            if service_metrics.get("success_rate", 100) < 90:
                report["critical_issues"].append(f"{service_name}: Low success rate ({service_metrics['success_rate']:.1f}%)")
                report["system_health"] = "degraded"
            
            avg_response = service_metrics.get("response_times", {}).get("average", 0)
            if avg_response > self.performance_thresholds['response_time_ms']:
                report["critical_issues"].append(f"{service_name}: High response time ({avg_response:.1f}ms)")
                if report["system_health"] == "good":
                    report["system_health"] = "degraded"
        
        # Generate overall recommendations
        if report["critical_issues"]:
            report["recommendations"].append("Address critical performance issues immediately")
        
        if report["system_health"] == "degraded":
            report["recommendations"].append("System performance is degraded - investigate and optimize")
        
        report["recommendations"].extend([
            "Continue monitoring performance trends",
            "Regular performance testing and optimization",
            "Consider infrastructure scaling if needed"
        ])
        
        return report
    
    async def optimize_recommendations(self, service_name: str = None) -> Dict[str, Any]:
        """Get specific optimization recommendations"""
        # Analyze current bottlenecks
        bottleneck_analysis = await self.analyze_bottlenecks(service_name)
        
        optimization_result = {
            "timestamp": datetime.now().isoformat(),
            "service": service_name or "all",
            "current_bottlenecks": bottleneck_analysis["bottlenecks_identified"],
            "immediate_actions": [],
            "long_term_optimizations": [],
            "estimated_impact": "medium"
        }
        
        # Immediate actions
        critical_bottlenecks = [b for b in bottleneck_analysis["bottlenecks_identified"] if b["severity"] == "critical"]
        if critical_bottlenecks:
            optimization_result["immediate_actions"].extend([
                "Restart failing services and investigate root causes",
                "Implement circuit breakers to prevent cascade failures",
                "Add health monitoring and alerting"
            ])
            optimization_result["estimated_impact"] = "high"
        
        high_bottlenecks = [b for b in bottleneck_analysis["bottlenecks_identified"] if b["severity"] == "high"]
        if high_bottlenecks:
            optimization_result["immediate_actions"].extend([
                "Optimize slow database queries and add indexing",
                "Implement caching for frequently accessed data",
                "Review and optimize algorithm efficiency"
            ])
        
        # Long-term optimizations
        optimization_result["long_term_optimizations"] = [
            "Implement microservice auto-scaling based on load",
            "Consider moving to containerized deployment for better resource management",
            "Implement distributed caching (Redis cluster)",
            "Add performance monitoring dashboards",
            "Regular performance regression testing in CI/CD pipeline"
        ]
        
        return optimization_result
    
    async def stress_test(self, service_name: str, max_concurrent: int = 50) -> Dict[str, Any]:
        """Run stress test to find service breaking point"""
        stress_results = {
            "service": service_name,
            "timestamp": datetime.now().isoformat(),
            "test_phases": [],
            "breaking_point": None,
            "recommendations": []
        }
        
        # Gradually increase load until failure
        concurrent_levels = [1, 5, 10, 20, 30, 40, 50]
        if max_concurrent > 50:
            concurrent_levels.extend(range(60, max_concurrent + 1, 10))
        
        for concurrent in concurrent_levels:
            self.logger.info(f'"service": "{service_name}", "concurrent_users": {concurrent}, "action": "stress_test_phase"')
            
            # Run load test at this concurrency level
            load_result = await self.run_load_test(
                service_name, 
                concurrent_users=concurrent, 
                duration_seconds=30
            )
            
            success_rate = (load_result.successful_requests / load_result.total_requests) * 100
            
            phase_result = {
                "concurrent_users": concurrent,
                "success_rate": success_rate,
                "average_response_time": load_result.average_response_time,
                "requests_per_second": load_result.requests_per_second,
                "status": "passed" if success_rate >= 95 else "degraded" if success_rate >= 80 else "failed"
            }
            
            stress_results["test_phases"].append(phase_result)
            
            # Check if this is the breaking point
            if success_rate < 80:  # Consider < 80% success rate as breaking point
                stress_results["breaking_point"] = {
                    "concurrent_users": concurrent,
                    "success_rate": success_rate,
                    "failure_reason": "success_rate_below_threshold"
                }
                break
            
            # Check if response time becomes unacceptable
            if load_result.average_response_time > 10000:  # 10 seconds
                stress_results["breaking_point"] = {
                    "concurrent_users": concurrent,
                    "average_response_time": load_result.average_response_time,
                    "failure_reason": "response_time_too_high"
                }
                break
        
        # Generate recommendations
        if stress_results["breaking_point"]:
            breaking_point = stress_results["breaking_point"]["concurrent_users"]
            stress_results["recommendations"] = [
                f"Service breaks at {breaking_point} concurrent users",
                "Implement load balancing for higher capacity",
                "Consider horizontal scaling solutions",
                "Add request queuing for load management"
            ]
        else:
            stress_results["recommendations"] = [
                f"Service handled up to {max_concurrent} concurrent users successfully",
                "Consider testing with higher loads if needed",
                "Current capacity appears adequate for expected load"
            ]
        
        return stress_results
    
    async def validate_sla(self, sla_requirements: Dict[str, Any] = None) -> Dict[str, Any]:
        """Validate services against SLA requirements"""
        # Default SLA requirements
        default_sla = {
            "availability": 99.0,  # 99% uptime
            "response_time_p95": 2000,  # 95th percentile < 2 seconds
            "response_time_p99": 5000,  # 99th percentile < 5 seconds
            "error_rate": 1.0  # < 1% error rate
        }
        
        sla = sla_requirements or default_sla
        
        validation_result = {
            "timestamp": datetime.now().isoformat(),
            "sla_requirements": sla,
            "service_compliance": {},
            "overall_compliance": True,
            "violations": []
        }
        
        # Check each service against SLA
        for service_name in self.monitored_services:
            service_metrics = await self.get_performance_metrics(service_name, hours=24)
            
            compliance = {
                "service": service_name,
                "compliant": True,
                "metrics": {},
                "violations": []
            }
            
            # Check availability (success rate)
            success_rate = service_metrics.get("success_rate", 0)
            compliance["metrics"]["availability"] = success_rate
            
            if success_rate < sla["availability"]:
                violation = f"Availability {success_rate:.1f}% below SLA {sla['availability']}%"
                compliance["violations"].append(violation)
                validation_result["violations"].append(f"{service_name}: {violation}")
                compliance["compliant"] = False
                validation_result["overall_compliance"] = False
            
            # Check response times
            response_times = service_metrics.get("response_times", {})
            p95 = response_times.get("p95", 0)
            p99 = response_times.get("p99", 0)
            
            compliance["metrics"]["response_time_p95"] = p95
            compliance["metrics"]["response_time_p99"] = p99
            
            if p95 > sla["response_time_p95"]:
                violation = f"P95 response time {p95:.1f}ms above SLA {sla['response_time_p95']}ms"
                compliance["violations"].append(violation)
                validation_result["violations"].append(f"{service_name}: {violation}")
                compliance["compliant"] = False
                validation_result["overall_compliance"] = False
            
            if p99 > sla["response_time_p99"]:
                violation = f"P99 response time {p99:.1f}ms above SLA {sla['response_time_p99']}ms"
                compliance["violations"].append(violation)
                validation_result["violations"].append(f"{service_name}: {violation}")
                compliance["compliant"] = False
                validation_result["overall_compliance"] = False
            
            # Error rate
            error_rate = 100 - success_rate
            compliance["metrics"]["error_rate"] = error_rate
            
            if error_rate > sla["error_rate"]:
                violation = f"Error rate {error_rate:.1f}% above SLA {sla['error_rate']}%"
                compliance["violations"].append(violation)
                validation_result["violations"].append(f"{service_name}: {violation}")
                compliance["compliant"] = False
                validation_result["overall_compliance"] = False
            
            validation_result["service_compliance"][service_name] = compliance
        
        return validation_result

async def main():
    service = PerformanceAnalysisService()
    await service.start_server()

if __name__ == "__main__":
    asyncio.run(main())
