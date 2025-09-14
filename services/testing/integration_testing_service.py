#!/usr/bin/env python3
"""
Integration Testing Service
Comprehensive testing of service-to-service communication and end-to-end workflows
"""
import asyncio
import json
import time
import sys
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.base_service import BaseService

@dataclass
class TestResult:
    test_name: str
    status: str  # "passed", "failed", "skipped", "error"
    execution_time: float
    result_data: Optional[Dict] = None
    error_message: Optional[str] = None
    timestamp: str = ""

@dataclass
class WorkflowTestResult:
    workflow_name: str
    total_steps: int
    passed_steps: int
    failed_steps: int
    execution_time: float
    step_results: List[TestResult]
    overall_status: str

class IntegrationTestingService(BaseService):
    """Integration testing service for microservices architecture"""

    def __init__(self):
        super().__init__("integration-test")
        self.test_results = {}
        self.workflow_results = {}
        self.test_suite_registry = {}
        
        # Register test methods
        self.register_handler("run_service_tests", self.run_service_tests)
        self.register_handler("run_workflow_tests", self.run_workflow_tests)
        self.register_handler("run_end_to_end_tests", self.run_end_to_end_tests)
        self.register_handler("run_load_tests", self.run_load_tests)
        self.register_handler("get_test_results", self.get_test_results)
        self.register_handler("run_compatibility_tests", self.run_compatibility_tests)
        self.register_handler("validate_service_contracts", self.validate_service_contracts)
        
        # Initialize test suites
        self._initialize_test_suites()

    def _initialize_test_suites(self):
        """Initialize predefined test suites"""
        self.test_suite_registry = {
            "service_health": {
                "description": "Basic health check for all services",
                "services": ["news-scraper", "market-data", "ml-model", "prediction", "scheduler", "paper-trading", "config-manager", "performance"],
                "tests": ["health_check", "basic_connectivity"]
            },
            "market_data_workflow": {
                "description": "Market data collection and processing workflow",
                "steps": [
                    {"service": "market-data", "method": "get_market_data", "params": {"symbol": "CBA.AX"}},
                    {"service": "market-data", "method": "get_technical_indicators", "params": {"symbol": "CBA.AX"}},
                    {"service": "market-data", "method": "validate_data_quality", "params": {"symbol": "CBA.AX"}}
                ]
            },
            "prediction_workflow": {
                "description": "Complete prediction generation workflow",
                "steps": [
                    {"service": "news-scraper", "method": "get_latest_news", "params": {"symbol": "CBA.AX"}},
                    {"service": "market-data", "method": "get_market_data", "params": {"symbol": "CBA.AX"}},
                    {"service": "ml-model", "method": "load_model", "params": {"symbol": "CBA.AX"}},
                    {"service": "prediction", "method": "generate_single_prediction", "params": {"symbol": "CBA.AX"}}
                ]
            },
            "paper_trading_workflow": {
                "description": "Paper trading execution workflow",
                "steps": [
                    {"service": "prediction", "method": "generate_single_prediction", "params": {"symbol": "CBA.AX"}},
                    {"service": "paper-trading", "method": "evaluate_trade_signal", "params": {"symbol": "CBA.AX", "action": "BUY"}},
                    {"service": "paper-trading", "method": "execute_paper_trade", "params": {"symbol": "CBA.AX", "action": "BUY", "quantity": 100}}
                ]
            }
        }

    async def run_service_tests(self, services: List[str] = None, test_types: List[str] = None):
        """Run comprehensive service tests"""
        if not services:
            services = ["news-scraper", "market-data", "ml-model", "prediction", "scheduler", "paper-trading", "config-manager", "performance"]
        
        if not test_types:
            test_types = ["health", "connectivity", "response_time", "error_handling"]

        test_session = {
            "session_id": f"service_test_{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "services": services,
            "test_types": test_types,
            "results": {},
            "summary": {}
        }

        self.logger.info(f'"action": "service_tests_started", "session_id": "{test_session["session_id"]}", "services": {len(services)}, "test_types": {test_types}"')

        for service in services:
            service_results = {}
            
            for test_type in test_types:
                test_result = await self._run_single_service_test(service, test_type)
                service_results[test_type] = test_result

            test_session["results"][service] = service_results

        # Generate summary
        test_session["summary"] = self._generate_service_test_summary(test_session["results"])
        
        # Store results
        self.test_results[test_session["session_id"]] = test_session
        
        self.logger.info(f'"action": "service_tests_completed", "session_id": "{test_session["session_id"]}", "passed": {test_session["summary"]["total_passed"]}, "failed": {test_session["summary"]["total_failed"]}"')
        
        return test_session

    async def _run_single_service_test(self, service: str, test_type: str) -> TestResult:
        """Run a single service test"""
        start_time = time.time()
        
        try:
            if test_type == "health":
                result = await self._test_service_health(service)
            elif test_type == "connectivity":
                result = await self._test_service_connectivity(service)
            elif test_type == "response_time":
                result = await self._test_service_response_time(service)
            elif test_type == "error_handling":
                result = await self._test_service_error_handling(service)
            else:
                result = {"error": f"Unknown test type: {test_type}"}

            execution_time = time.time() - start_time
            
            if "error" in result:
                return TestResult(
                    test_name=f"{service}_{test_type}",
                    status="failed",
                    execution_time=execution_time,
                    error_message=result["error"],
                    timestamp=datetime.now().isoformat()
                )
            else:
                return TestResult(
                    test_name=f"{service}_{test_type}",
                    status="passed",
                    execution_time=execution_time,
                    result_data=result,
                    timestamp=datetime.now().isoformat()
                )

        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                test_name=f"{service}_{test_type}",
                status="error",
                execution_time=execution_time,
                error_message=str(e),
                timestamp=datetime.now().isoformat()
            )

    async def _test_service_health(self, service: str) -> Dict:
        """Test service health endpoint"""
        try:
            health_result = await self.call_service(service, "health", timeout=5.0)
            
            if health_result.get("status") == "healthy":
                return {"status": "healthy", "details": health_result}
            else:
                return {"error": f"Service {service} is not healthy: {health_result.get('status', 'unknown')}"}
                
        except Exception as e:
            return {"error": f"Health check failed: {e}"}

    async def _test_service_connectivity(self, service: str) -> Dict:
        """Test basic service connectivity"""
        try:
            # Test basic method call
            start_time = time.time()
            await self.call_service(service, "health", timeout=10.0)
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return {
                "connectivity": "success",
                "response_time_ms": response_time
            }
            
        except Exception as e:
            return {"error": f"Connectivity test failed: {e}"}

    async def _test_service_response_time(self, service: str) -> Dict:
        """Test service response time performance"""
        response_times = []
        
        for i in range(5):  # 5 test calls
            try:
                start_time = time.time()
                await self.call_service(service, "health", timeout=10.0)
                response_time = (time.time() - start_time) * 1000
                response_times.append(response_time)
                
            except Exception:
                continue  # Skip failed calls for response time calculation

        if not response_times:
            return {"error": "No successful calls for response time measurement"}

        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)

        return {
            "average_response_time_ms": avg_response_time,
            "max_response_time_ms": max_response_time,
            "min_response_time_ms": min_response_time,
            "successful_calls": len(response_times),
            "performance_rating": "excellent" if avg_response_time < 100 else "good" if avg_response_time < 500 else "poor"
        }

    async def _test_service_error_handling(self, service: str) -> Dict:
        """Test service error handling capabilities"""
        error_tests = [
            {"method": "invalid_method", "expected": "method_not_found"},
            {"method": "health", "params": {"invalid_param": "test"}, "expected": "handled_gracefully"}
        ]

        error_handling_results = {}
        
        for test in error_tests:
            try:
                result = await self.call_service(
                    service, 
                    test["method"], 
                    timeout=5.0,
                    **test.get("params", {})
                )
                
                # If we get a result, check if error was handled gracefully
                if "error" in str(result).lower():
                    error_handling_results[test["method"]] = "handled_gracefully"
                else:
                    error_handling_results[test["method"]] = "unexpected_success"
                    
            except Exception as e:
                if "unknown method" in str(e).lower() or "method not found" in str(e).lower():
                    error_handling_results[test["method"]] = "handled_gracefully"
                else:
                    error_handling_results[test["method"]] = f"unhandled_error: {e}"

        return {
            "error_handling_tests": error_handling_results,
            "overall_error_handling": "good" if all("handled" in result for result in error_handling_results.values()) else "needs_improvement"
        }

    def _generate_service_test_summary(self, results: Dict) -> Dict:
        """Generate summary of service test results"""
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_errors = 0
        
        service_summary = {}
        
        for service, service_results in results.items():
            service_passed = 0
            service_total = len(service_results)
            
            for test_type, test_result in service_results.items():
                total_tests += 1
                if test_result.status == "passed":
                    total_passed += 1
                    service_passed += 1
                elif test_result.status == "failed":
                    total_failed += 1
                elif test_result.status == "error":
                    total_errors += 1
            
            service_summary[service] = {
                "passed": service_passed,
                "total": service_total,
                "success_rate": (service_passed / service_total * 100) if service_total > 0 else 0
            }

        return {
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "total_errors": total_errors,
            "overall_success_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0,
            "service_summary": service_summary
        }

    async def run_workflow_tests(self, workflows: List[str] = None):
        """Run end-to-end workflow tests"""
        if not workflows:
            workflows = list(self.test_suite_registry.keys())

        workflow_session = {
            "session_id": f"workflow_test_{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "workflows": workflows,
            "results": {},
            "summary": {}
        }

        self.logger.info(f'"action": "workflow_tests_started", "session_id": "{workflow_session["session_id"]}", "workflows": {workflows}"')

        for workflow_name in workflows:
            if workflow_name in self.test_suite_registry:
                workflow_result = await self._run_workflow_test(workflow_name)
                workflow_session["results"][workflow_name] = workflow_result

        # Generate summary
        workflow_session["summary"] = self._generate_workflow_summary(workflow_session["results"])
        
        # Store results
        self.workflow_results[workflow_session["session_id"]] = workflow_session

        self.logger.info(f'"action": "workflow_tests_completed", "session_id": "{workflow_session["session_id"]}", "successful_workflows": {workflow_session["summary"]["successful_workflows"]}"')

        return workflow_session

    async def _run_workflow_test(self, workflow_name: str) -> WorkflowTestResult:
        """Run a single workflow test"""
        workflow_config = self.test_suite_registry[workflow_name]
        start_time = time.time()
        
        step_results = []
        passed_steps = 0
        failed_steps = 0

        if "steps" in workflow_config:
            # Sequential workflow steps
            for i, step in enumerate(workflow_config["steps"]):
                step_name = f"{workflow_name}_step_{i+1}"
                
                try:
                    step_start = time.time()
                    result = await self.call_service(
                        step["service"], 
                        step["method"], 
                        timeout=30.0,
                        **step.get("params", {})
                    )
                    step_time = time.time() - step_start
                    
                    step_result = TestResult(
                        test_name=step_name,
                        status="passed",
                        execution_time=step_time,
                        result_data=result,
                        timestamp=datetime.now().isoformat()
                    )
                    passed_steps += 1
                    
                except Exception as e:
                    step_time = time.time() - step_start
                    step_result = TestResult(
                        test_name=step_name,
                        status="failed",
                        execution_time=step_time,
                        error_message=str(e),
                        timestamp=datetime.now().isoformat()
                    )
                    failed_steps += 1

                step_results.append(step_result)

        elif "services" in workflow_config and "tests" in workflow_config:
            # Service-based workflow
            for service in workflow_config["services"]:
                for test in workflow_config["tests"]:
                    step_name = f"{workflow_name}_{service}_{test}"
                    
                    try:
                        step_start = time.time()
                        if test == "health_check":
                            result = await self.call_service(service, "health", timeout=10.0)
                        elif test == "basic_connectivity":
                            result = await self._test_service_connectivity(service)
                        else:
                            result = {"error": f"Unknown test: {test}"}
                        
                        step_time = time.time() - step_start
                        
                        if "error" in result:
                            step_result = TestResult(
                                test_name=step_name,
                                status="failed",
                                execution_time=step_time,
                                error_message=str(result["error"]),
                                timestamp=datetime.now().isoformat()
                            )
                            failed_steps += 1
                        else:
                            step_result = TestResult(
                                test_name=step_name,
                                status="passed",
                                execution_time=step_time,
                                result_data=result,
                                timestamp=datetime.now().isoformat()
                            )
                            passed_steps += 1
                            
                    except Exception as e:
                        step_time = time.time() - step_start
                        step_result = TestResult(
                            test_name=step_name,
                            status="failed",
                            execution_time=step_time,
                            error_message=str(e),
                            timestamp=datetime.now().isoformat()
                        )
                        failed_steps += 1

                    step_results.append(step_result)

        total_time = time.time() - start_time
        total_steps = len(step_results)
        
        overall_status = "passed" if failed_steps == 0 else "partial" if passed_steps > 0 else "failed"

        return WorkflowTestResult(
            workflow_name=workflow_name,
            total_steps=total_steps,
            passed_steps=passed_steps,
            failed_steps=failed_steps,
            execution_time=total_time,
            step_results=step_results,
            overall_status=overall_status
        )

    def _generate_workflow_summary(self, results: Dict) -> Dict:
        """Generate workflow test summary"""
        total_workflows = len(results)
        successful_workflows = sum(1 for result in results.values() if result.overall_status == "passed")
        partial_workflows = sum(1 for result in results.values() if result.overall_status == "partial")
        failed_workflows = sum(1 for result in results.values() if result.overall_status == "failed")

        return {
            "total_workflows": total_workflows,
            "successful_workflows": successful_workflows,
            "partial_workflows": partial_workflows,
            "failed_workflows": failed_workflows,
            "success_rate": (successful_workflows / total_workflows * 100) if total_workflows > 0 else 0
        }

    async def run_end_to_end_tests(self):
        """Run comprehensive end-to-end system tests"""
        e2e_session = {
            "session_id": f"e2e_test_{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "summary": {}
        }

        self.logger.info(f'"action": "e2e_tests_started", "session_id": "{e2e_session["session_id"]}"')

        # Test 1: Complete prediction generation workflow
        e2e_session["tests"]["complete_prediction"] = await self._test_complete_prediction_workflow()
        
        # Test 2: Paper trading workflow
        e2e_session["tests"]["paper_trading"] = await self._test_paper_trading_workflow()
        
        # Test 3: Configuration management workflow
        e2e_session["tests"]["config_management"] = await self._test_config_management_workflow()
        
        # Test 4: Performance monitoring workflow
        e2e_session["tests"]["performance_monitoring"] = await self._test_performance_monitoring_workflow()

        # Generate summary
        passed_tests = sum(1 for test in e2e_session["tests"].values() if test.status == "passed")
        total_tests = len(e2e_session["tests"])
        
        e2e_session["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
        }

        self.logger.info(f'"action": "e2e_tests_completed", "session_id": "{e2e_session["session_id"]}", "success_rate": {e2e_session["summary"]["success_rate"]:.1f}"')

        return e2e_session

    async def _test_complete_prediction_workflow(self) -> TestResult:
        """Test complete prediction generation workflow"""
        start_time = time.time()
        workflow_steps = []
        
        try:
            # Step 1: Get market data
            market_data = await self.call_service("market-data", "get_market_data", symbol="CBA.AX", timeout=15.0)
            workflow_steps.append({"step": "market_data", "status": "success", "data_keys": list(market_data.keys()) if isinstance(market_data, dict) else None})
            
            # Step 2: Get news sentiment
            news_data = await self.call_service("news-scraper", "get_latest_news", symbol="CBA.AX", timeout=15.0)
            workflow_steps.append({"step": "news_sentiment", "status": "success", "articles": len(news_data) if isinstance(news_data, list) else None})
            
            # Step 3: Generate prediction
            prediction = await self.call_service("prediction", "generate_single_prediction", symbol="CBA.AX", timeout=20.0)
            workflow_steps.append({"step": "prediction", "status": "success", "prediction_data": prediction})
            
            execution_time = time.time() - start_time
            
            return TestResult(
                test_name="complete_prediction_workflow",
                status="passed",
                execution_time=execution_time,
                result_data={"workflow_steps": workflow_steps},
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                test_name="complete_prediction_workflow",
                status="failed",
                execution_time=execution_time,
                error_message=str(e),
                timestamp=datetime.now().isoformat()
            )

    async def _test_paper_trading_workflow(self) -> TestResult:
        """Test paper trading workflow"""
        start_time = time.time()
        
        try:
            # Generate a prediction first
            prediction = await self.call_service("prediction", "generate_single_prediction", symbol="CBA.AX", timeout=20.0)
            
            # Try to execute a paper trade
            trade_result = await self.call_service("paper-trading", "execute_paper_trade", 
                                                 symbol="CBA.AX", action="BUY", quantity=100, timeout=15.0)
            
            execution_time = time.time() - start_time
            
            return TestResult(
                test_name="paper_trading_workflow",
                status="passed",
                execution_time=execution_time,
                result_data={"prediction": prediction, "trade_result": trade_result},
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                test_name="paper_trading_workflow",
                status="failed",
                execution_time=execution_time,
                error_message=str(e),
                timestamp=datetime.now().isoformat()
            )

    async def _test_config_management_workflow(self) -> TestResult:
        """Test configuration management workflow"""
        start_time = time.time()
        
        try:
            # Validate configurations
            config_status = await self.call_service("config-manager", "validate_config_consistency", timeout=15.0)
            
            # Generate config report
            config_report = await self.call_service("config-manager", "generate_config_report", timeout=15.0)
            
            execution_time = time.time() - start_time
            
            return TestResult(
                test_name="config_management_workflow",
                status="passed",
                execution_time=execution_time,
                result_data={"config_status": config_status, "config_report": config_report},
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                test_name="config_management_workflow",
                status="failed",
                execution_time=execution_time,
                error_message=str(e),
                timestamp=datetime.now().isoformat()
            )

    async def _test_performance_monitoring_workflow(self) -> TestResult:
        """Test performance monitoring workflow"""
        start_time = time.time()
        
        try:
            # Get performance metrics
            metrics = await self.call_service("performance", "collect_performance_metrics", timeout=15.0)
            
            # Run performance analysis
            analysis = await self.call_service("performance", "analyze_performance", timeout=15.0)
            
            execution_time = time.time() - start_time
            
            return TestResult(
                test_name="performance_monitoring_workflow",
                status="passed",
                execution_time=execution_time,
                result_data={"metrics": metrics, "analysis": analysis},
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                test_name="performance_monitoring_workflow",
                status="failed",
                execution_time=execution_time,
                error_message=str(e),
                timestamp=datetime.now().isoformat()
            )

    async def run_load_tests(self, concurrent_users: int = 5, duration_seconds: int = 60):
        """Run load tests against the microservices"""
        load_test_session = {
            "session_id": f"load_test_{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "config": {
                "concurrent_users": concurrent_users,
                "duration_seconds": duration_seconds
            },
            "results": {}
        }

        self.logger.info(f'"action": "load_tests_started", "session_id": "{load_test_session["session_id"]}", "concurrent_users": {concurrent_users}, "duration": {duration_seconds}"')

        # Run concurrent load tests
        tasks = []
        for i in range(concurrent_users):
            task = asyncio.create_task(self._run_load_test_user(i, duration_seconds))
            tasks.append(task)

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful_users = 0
        total_requests = 0
        total_errors = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                load_test_session["results"][f"user_{i}"] = {"error": str(result)}
                total_errors += 1
            else:
                load_test_session["results"][f"user_{i}"] = result
                successful_users += 1
                total_requests += result.get("total_requests", 0)
                total_errors += result.get("errors", 0)

        # Calculate summary statistics
        load_test_session["summary"] = {
            "successful_users": successful_users,
            "total_users": concurrent_users,
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": (total_errors / total_requests * 100) if total_requests > 0 else 0,
            "requests_per_second": total_requests / duration_seconds if duration_seconds > 0 else 0
        }

        self.logger.info(f'"action": "load_tests_completed", "session_id": "{load_test_session["session_id"]}", "rps": {load_test_session["summary"]["requests_per_second"]:.2f}, "error_rate": {load_test_session["summary"]["error_rate"]:.2f}%"')

        return load_test_session

    async def _run_load_test_user(self, user_id: int, duration_seconds: int) -> Dict:
        """Simulate a single user for load testing"""
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        requests = 0
        errors = 0
        response_times = []
        
        while time.time() < end_time:
            try:
                request_start = time.time()
                
                # Simulate typical user workflow
                await self.call_service("prediction", "generate_single_prediction", symbol="CBA.AX", timeout=10.0)
                
                response_time = (time.time() - request_start) * 1000
                response_times.append(response_time)
                requests += 1
                
                # Small delay between requests
                await asyncio.sleep(0.1)
                
            except Exception:
                errors += 1
                
        return {
            "user_id": user_id,
            "total_requests": requests,
            "errors": errors,
            "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0
        }

    async def get_test_results(self, session_id: str = None, test_type: str = "all"):
        """Get test results for specified session or all recent results"""
        if session_id:
            if session_id in self.test_results:
                return self.test_results[session_id]
            elif session_id in self.workflow_results:
                return self.workflow_results[session_id]
            else:
                return {"error": f"Session {session_id} not found"}
        
        # Return summary of all recent results
        results_summary = {
            "timestamp": datetime.now().isoformat(),
            "service_test_sessions": len(self.test_results),
            "workflow_test_sessions": len(self.workflow_results),
            "recent_service_tests": list(self.test_results.keys())[-5:],
            "recent_workflow_tests": list(self.workflow_results.keys())[-5:]
        }
        
        return results_summary

    async def run_compatibility_tests(self):
        """Run compatibility tests with existing system"""
        compatibility_session = {
            "session_id": f"compatibility_test_{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "summary": {}
        }

        # Test database compatibility
        compatibility_session["tests"]["database_compatibility"] = await self._test_database_compatibility()
        
        # Test API compatibility
        compatibility_session["tests"]["api_compatibility"] = await self._test_api_compatibility()
        
        # Test configuration compatibility
        compatibility_session["tests"]["config_compatibility"] = await self._test_config_compatibility()

        # Generate summary
        passed_tests = sum(1 for test in compatibility_session["tests"].values() if test.status == "passed")
        total_tests = len(compatibility_session["tests"])
        
        compatibility_session["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "compatibility_score": (passed_tests / total_tests * 100) if total_tests > 0 else 0
        }

        return compatibility_session

    async def _test_database_compatibility(self) -> TestResult:
        """Test database compatibility with existing schemas"""
        start_time = time.time()
        
        try:
            # Test database validation service
            db_validation = await self.call_service("database-validator", "validate_all_schemas", timeout=20.0)
            
            execution_time = time.time() - start_time
            
            return TestResult(
                test_name="database_compatibility",
                status="passed" if db_validation.get("overall_status") == "valid" else "failed",
                execution_time=execution_time,
                result_data=db_validation,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                test_name="database_compatibility",
                status="failed",
                execution_time=execution_time,
                error_message=str(e),
                timestamp=datetime.now().isoformat()
            )

    async def _test_api_compatibility(self) -> TestResult:
        """Test API compatibility with existing interfaces"""
        start_time = time.time()
        
        try:
            # Test that all services respond to expected methods
            api_tests = {}
            
            # Test prediction service API
            prediction_result = await self.call_service("prediction", "generate_single_prediction", symbol="CBA.AX", timeout=15.0)
            api_tests["prediction_api"] = "compatible" if "confidence" in str(prediction_result) else "incompatible"
            
            # Test market data API
            market_result = await self.call_service("market-data", "get_market_data", symbol="CBA.AX", timeout=15.0)
            api_tests["market_data_api"] = "compatible" if "technical" in str(market_result) else "incompatible"
            
            execution_time = time.time() - start_time
            
            compatible_apis = sum(1 for status in api_tests.values() if status == "compatible")
            total_apis = len(api_tests)
            
            return TestResult(
                test_name="api_compatibility",
                status="passed" if compatible_apis == total_apis else "failed",
                execution_time=execution_time,
                result_data={"api_tests": api_tests, "compatibility_rate": (compatible_apis / total_apis * 100)},
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                test_name="api_compatibility",
                status="failed",
                execution_time=execution_time,
                error_message=str(e),
                timestamp=datetime.now().isoformat()
            )

    async def _test_config_compatibility(self) -> TestResult:
        """Test configuration compatibility"""
        start_time = time.time()
        
        try:
            config_consistency = await self.call_service("config-manager", "validate_config_consistency", timeout=15.0)
            
            execution_time = time.time() - start_time
            
            return TestResult(
                test_name="config_compatibility",
                status="passed" if config_consistency.get("consistency_score", 0) >= 80 else "failed",
                execution_time=execution_time,
                result_data=config_consistency,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                test_name="config_compatibility",
                status="failed",
                execution_time=execution_time,
                error_message=str(e),
                timestamp=datetime.now().isoformat()
            )

    async def validate_service_contracts(self):
        """Validate service contracts and interfaces"""
        contract_validation = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "contract_violations": [],
            "summary": {}
        }

        services = ["news-scraper", "market-data", "ml-model", "prediction", "scheduler", "paper-trading"]
        
        for service in services:
            try:
                # Get service health to verify it's running
                health = await self.call_service(service, "health", timeout=5.0)
                
                # Verify expected methods exist by calling them
                contract_validation["services"][service] = {
                    "health_check": "passed",
                    "expected_methods": await self._check_service_methods(service)
                }
                
            except Exception as e:
                contract_validation["services"][service] = {
                    "health_check": "failed",
                    "error": str(e)
                }
                contract_validation["contract_violations"].append({
                    "service": service,
                    "violation": "Service unreachable",
                    "details": str(e)
                })

        # Generate summary
        healthy_services = sum(1 for s in contract_validation["services"].values() if s.get("health_check") == "passed")
        total_services = len(contract_validation["services"])
        
        contract_validation["summary"] = {
            "total_services": total_services,
            "healthy_services": healthy_services,
            "contract_violations": len(contract_validation["contract_violations"]),
            "contract_compliance": (healthy_services / total_services * 100) if total_services > 0 else 0
        }

        return contract_validation

    async def _check_service_methods(self, service: str) -> Dict:
        """Check if service implements expected methods"""
        expected_methods = {
            "news-scraper": ["get_latest_news", "analyze_sentiment"],
            "market-data": ["get_market_data", "get_technical_indicators"],
            "ml-model": ["load_model", "predict"],
            "prediction": ["generate_single_prediction", "generate_predictions"],
            "scheduler": ["schedule_job", "get_scheduled_jobs"],
            "paper-trading": ["execute_paper_trade", "get_positions"]
        }

        service_methods = expected_methods.get(service, [])
        method_results = {}
        
        for method in service_methods:
            try:
                # Try calling the method (may fail due to parameters, but should not fail due to method not existing)
                await self.call_service(service, method, timeout=5.0)
                method_results[method] = "exists"
            except Exception as e:
                if "unknown method" in str(e).lower() or "method not found" in str(e).lower():
                    method_results[method] = "missing"
                else:
                    method_results[method] = "exists_but_failed"  # Method exists but failed due to parameters

        return method_results

    async def health_check(self):
        """Enhanced health check with integration test status"""
        base_health = await super().health_check()
        
        integration_health = {
            **base_health,
            "test_sessions": len(self.test_results) + len(self.workflow_results),
            "test_suites": len(self.test_suite_registry),
            "recent_test_results": "available" if self.test_results or self.workflow_results else "none"
        }

        return integration_health

async def main():
    service = IntegrationTestingService()
    await service.start_server()

if __name__ == "__main__":
    asyncio.run(main())
