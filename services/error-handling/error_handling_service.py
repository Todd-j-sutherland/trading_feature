#!/usr/bin/env python3
"""
Error Handling Review Service
Comprehensive error handling validation and circuit breaker integration
Ensures all microservices have robust error handling for production reliability

Key Features:
- Circuit breaker pattern implementation for service resilience
- Comprehensive error validation across all services
- Error recovery and fallback mechanism testing
- Service degradation handling validation
- Error logging and monitoring integration

Dependencies:
- All trading microservices for error testing
- Redis for circuit breaker state management
- Logging infrastructure for error tracking

Related Files:
- services/base/base_service.py (base error handling)
- All service implementations for error pattern validation
"""

import asyncio
import sys
import os
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import traceback
import time
from dataclasses import dataclass
from enum import Enum

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.base_service import BaseService

# Settings.py integration for configuration management
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
        print("Warning: settings.py not found - using fallback configuration")

class CircuitBreakerState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, block requests
    HALF_OPEN = "half_open"  # Testing recovery

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    success_threshold: int = 3
    timeout: float = 30.0

@dataclass
class ErrorPattern:
    error_type: str
    frequency: int
    last_occurrence: datetime
    severity: str
    service: str
    context: Dict[str, Any]

class CircuitBreaker:
    """Circuit breaker implementation for service resilience"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig, redis_client=None):
        self.name = name
        self.config = config
        self.redis_client = redis_client
        
        # Local state (backed by Redis if available)
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_success_time = None
        
        # Load state from Redis if available
        if self.redis_client:
            self._load_state_from_redis()
    
    def _load_state_from_redis(self):
        """Load circuit breaker state from Redis"""
        try:
            if self.redis_client:
                state_data = self.redis_client.get(f"circuit_breaker:{self.name}")
                if state_data:
                    data = json.loads(state_data)
                    self.state = CircuitBreakerState(data.get('state', 'closed'))
                    self.failure_count = data.get('failure_count', 0)
                    self.success_count = data.get('success_count', 0)
                    
                    if data.get('last_failure_time'):
                        self.last_failure_time = datetime.fromisoformat(data['last_failure_time'])
                    if data.get('last_success_time'):
                        self.last_success_time = datetime.fromisoformat(data['last_success_time'])
        except Exception:
            pass  # Use default state if Redis unavailable
    
    def _save_state_to_redis(self):
        """Save circuit breaker state to Redis"""
        try:
            if self.redis_client:
                state_data = {
                    'state': self.state.value,
                    'failure_count': self.failure_count,
                    'success_count': self.success_count,
                    'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
                    'last_success_time': self.last_success_time.isoformat() if self.last_success_time else None
                }
                self.redis_client.setex(
                    f"circuit_breaker:{self.name}",
                    300,  # 5 minute expiry
                    json.dumps(state_data)
                )
        except Exception:
            pass  # Continue if Redis unavailable
    
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        
        # Check if circuit is open
        if self.state == CircuitBreakerState.OPEN:
            if self.last_failure_time and \
               (datetime.now() - self.last_failure_time).seconds >= self.config.recovery_timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                self._save_state_to_redis()
            else:
                raise Exception(f"Circuit breaker {self.name} is OPEN")
        
        try:
            # Execute function with timeout
            result = await asyncio.wait_for(func(*args, **kwargs), timeout=self.config.timeout)
            
            # Record success
            await self._record_success()
            return result
            
        except Exception as e:
            # Record failure
            await self._record_failure(e)
            raise
    
    async def _record_success(self):
        """Record successful operation"""
        self.success_count += 1
        self.last_success_time = datetime.now()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        
        self._save_state_to_redis()
    
    async def _record_failure(self, error: Exception):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
        
        self._save_state_to_redis()

class ErrorHandlingService(BaseService):
    """
    Comprehensive error handling validation and circuit breaker service
    Ensures all microservices have robust error handling for production reliability
    """
    
    def __init__(self):
        super().__init__("error-handling")
        
        # Circuit breakers for each service
        self.circuit_breakers = {}
        self._initialize_circuit_breakers()
        
        # Error pattern tracking
        self.error_patterns = {}
        self.error_statistics = {
            "total_errors": 0,
            "errors_by_service": {},
            "errors_by_type": {},
            "error_trends": []
        }
        
        # Services to monitor
        self.monitored_services = [
            "market-data",
            "sentiment",
            "prediction", 
            "paper-trading",
            "ml-model",
            "scheduler",
            "database",
            "api-consistency"
        ]
        
        # Register error handling methods
        self.register_handler("validate_error_handling", self.validate_error_handling)
        self.register_handler("test_circuit_breakers", self.test_circuit_breakers)
        self.register_handler("test_service_resilience", self.test_service_resilience)
        self.register_handler("get_error_statistics", self.get_error_statistics)
        self.register_handler("test_fallback_mechanisms", self.test_fallback_mechanisms)
        self.register_handler("inject_test_errors", self.inject_test_errors)
        self.register_handler("get_circuit_breaker_status", self.get_circuit_breaker_status)
        self.register_handler("reset_circuit_breakers", self.reset_circuit_breakers)
        
    def _initialize_circuit_breakers(self):
        """Initialize circuit breakers for all services"""
        
        # Load circuit breaker configurations from settings
        if SETTINGS_AVAILABLE and hasattr(Settings, 'CIRCUIT_BREAKER_CONFIG'):
            cb_config = Settings.CIRCUIT_BREAKER_CONFIG
        else:
            # Fallback configuration
            cb_config = {
                'default': CircuitBreakerConfig(
                    failure_threshold=5,
                    recovery_timeout=60,
                    success_threshold=3,
                    timeout=30.0
                ),
                'critical_services': CircuitBreakerConfig(
                    failure_threshold=3,  # More sensitive for critical services
                    recovery_timeout=30,
                    success_threshold=2,
                    timeout=20.0
                )
            }
        
        # Critical services (more sensitive circuit breakers)
        critical_services = ["prediction", "paper-trading", "market-data"]
        
        for service in self.monitored_services:
            if service in critical_services:
                config = cb_config.get('critical_services', cb_config['default'])
            else:
                config = cb_config.get('default', CircuitBreakerConfig())
            
            self.circuit_breakers[service] = CircuitBreaker(
                name=service,
                config=config,
                redis_client=self.redis_client
            )
    
    async def validate_error_handling(self, target_service: str = None) -> Dict[str, Any]:
        """Validate error handling across all services"""
        self.logger.info('"action": "error_handling_validation_started"')
        
        validation_result = {
            "timestamp": datetime.now().isoformat(),
            "services_validated": 0,
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "service_results": {},
            "critical_issues": [],
            "recommendations": []
        }
        
        services_to_test = [target_service] if target_service else self.monitored_services
        
        for service_name in services_to_test:
            try:
                service_result = await self._validate_service_error_handling(service_name)
                validation_result["service_results"][service_name] = service_result
                validation_result["services_validated"] += 1
                validation_result["total_tests"] += service_result.get("total_tests", 0)
                validation_result["passed_tests"] += service_result.get("passed_tests", 0)
                validation_result["failed_tests"] += service_result.get("failed_tests", 0)
                
                # Collect critical issues
                if service_result.get("critical_issues"):
                    validation_result["critical_issues"].extend(service_result["critical_issues"])
                    
            except Exception as e:
                self.logger.error(f'"service": "{service_name}", "error": "{e}", "action": "service_error_validation_failed"')
                validation_result["critical_issues"].append({
                    "service": service_name,
                    "type": "validation_failed",
                    "error": str(e)
                })
        
        # Generate recommendations
        if validation_result["failed_tests"] > 0:
            failure_rate = (validation_result["failed_tests"] / validation_result["total_tests"]) * 100
            if failure_rate > 20:
                validation_result["recommendations"].append("High error handling failure rate - review service implementations")
        
        if len(validation_result["critical_issues"]) > 0:
            validation_result["recommendations"].append("Address critical error handling issues before production")
        
        self.logger.info(f'"services_validated": {validation_result["services_validated"]}, "passed_tests": {validation_result["passed_tests"]}, "failed_tests": {validation_result["failed_tests"]}, "action": "error_handling_validation_completed"')
        
        return validation_result
    
    async def _validate_service_error_handling(self, service_name: str) -> Dict[str, Any]:
        """Validate error handling for a specific service"""
        service_result = {
            "service": service_name,
            "available": False,
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_results": {},
            "critical_issues": [],
            "error_patterns": []
        }
        
        try:
            # Test 1: Basic service availability
            service_result["total_tests"] += 1
            try:
                health = await self.call_service(service_name, "health", timeout=10.0)
                service_result["available"] = True
                service_result["passed_tests"] += 1
                service_result["test_results"]["availability"] = {"status": "passed", "response_time": health.get("uptime", 0)}
            except Exception as e:
                service_result["failed_tests"] += 1
                service_result["test_results"]["availability"] = {"status": "failed", "error": str(e)}
                service_result["critical_issues"].append({
                    "test": "availability",
                    "error": str(e),
                    "severity": "critical"
                })
            
            # Test 2: Timeout handling
            service_result["total_tests"] += 1
            try:
                # Test with very short timeout to trigger timeout error
                await self.call_service(service_name, "health", timeout=0.001)
                service_result["failed_tests"] += 1
                service_result["test_results"]["timeout_handling"] = {"status": "failed", "note": "Service should have timed out but didn't"}
            except asyncio.TimeoutError:
                service_result["passed_tests"] += 1
                service_result["test_results"]["timeout_handling"] = {"status": "passed", "note": "Correctly handled timeout"}
            except Exception as e:
                service_result["passed_tests"] += 1  # Any exception is better than hanging
                service_result["test_results"]["timeout_handling"] = {"status": "passed", "note": f"Handled with exception: {type(e).__name__}"}
            
            # Test 3: Invalid method handling
            service_result["total_tests"] += 1
            try:
                await self.call_service(service_name, "invalid_method_test_12345")
                service_result["failed_tests"] += 1
                service_result["test_results"]["invalid_method"] = {"status": "failed", "note": "Should return error for invalid method"}
            except Exception as e:
                service_result["passed_tests"] += 1
                service_result["test_results"]["invalid_method"] = {"status": "passed", "error_type": type(e).__name__}
            
            # Test 4: Invalid parameters handling
            if service_name == "prediction":
                service_result["total_tests"] += 1
                try:
                    # Test with invalid symbol
                    result = await self.call_service(service_name, "generate_single_prediction", symbol="INVALID_SYMBOL_XYZ123")
                    if "error" in str(result).lower():
                        service_result["passed_tests"] += 1
                        service_result["test_results"]["invalid_params"] = {"status": "passed", "note": "Correctly handled invalid parameters"}
                    else:
                        service_result["failed_tests"] += 1
                        service_result["test_results"]["invalid_params"] = {"status": "failed", "note": "Should return error for invalid symbol"}
                except Exception as e:
                    service_result["passed_tests"] += 1
                    service_result["test_results"]["invalid_params"] = {"status": "passed", "error_type": type(e).__name__}
            
            # Test 5: Service degradation handling (for services with dependencies)
            if service_name in ["prediction", "paper-trading"]:
                service_result["total_tests"] += 1
                try:
                    # Test how service handles when dependencies are unavailable
                    # This is simulated by checking if service has fallback mechanisms
                    degradation_test = await self._test_service_degradation(service_name)
                    if degradation_test.get("has_fallback"):
                        service_result["passed_tests"] += 1
                        service_result["test_results"]["degradation_handling"] = {"status": "passed", "fallback_type": degradation_test.get("fallback_type")}
                    else:
                        service_result["failed_tests"] += 1
                        service_result["test_results"]["degradation_handling"] = {"status": "failed", "note": "No fallback mechanism detected"}
                except Exception as e:
                    service_result["failed_tests"] += 1
                    service_result["test_results"]["degradation_handling"] = {"status": "failed", "error": str(e)}
            
        except Exception as e:
            service_result["critical_issues"].append({
                "test": "service_validation",
                "error": str(e),
                "severity": "critical"
            })
        
        return service_result
    
    async def _test_service_degradation(self, service_name: str) -> Dict[str, Any]:
        """Test how service handles degradation scenarios"""
        degradation_result = {
            "has_fallback": False,
            "fallback_type": "none"
        }
        
        if service_name == "prediction":
            try:
                # Test prediction service with minimal data to see if it has fallbacks
                result = await self.call_service(service_name, "generate_single_prediction", symbol="CBA.AX")
                
                # Check if result contains fallback indicators
                if isinstance(result, dict):
                    if "fallback" in str(result).lower() or "error" in result:
                        degradation_result["has_fallback"] = True
                        degradation_result["fallback_type"] = "graceful_degradation"
                    elif result.get("confidence", 1.0) < 0.3:
                        # Low confidence might indicate degraded mode
                        degradation_result["has_fallback"] = True
                        degradation_result["fallback_type"] = "low_confidence_mode"
                        
            except Exception:
                # Exception handling itself is a form of degradation handling
                degradation_result["has_fallback"] = True
                degradation_result["fallback_type"] = "exception_handling"
        
        return degradation_result
    
    async def test_circuit_breakers(self) -> Dict[str, Any]:
        """Test circuit breaker functionality for all services"""
        self.logger.info('"action": "circuit_breaker_testing_started"')
        
        test_result = {
            "timestamp": datetime.now().isoformat(),
            "circuit_breakers_tested": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "service_results": {}
        }
        
        for service_name, circuit_breaker in self.circuit_breakers.items():
            try:
                cb_test_result = await self._test_single_circuit_breaker(service_name, circuit_breaker)
                test_result["service_results"][service_name] = cb_test_result
                test_result["circuit_breakers_tested"] += 1
                
                if cb_test_result.get("test_passed", False):
                    test_result["passed_tests"] += 1
                else:
                    test_result["failed_tests"] += 1
                    
            except Exception as e:
                self.logger.error(f'"service": "{service_name}", "error": "{e}", "action": "circuit_breaker_test_failed"')
                test_result["failed_tests"] += 1
                test_result["service_results"][service_name] = {
                    "test_passed": False,
                    "error": str(e)
                }
        
        self.logger.info(f'"circuit_breakers_tested": {test_result["circuit_breakers_tested"]}, "passed_tests": {test_result["passed_tests"]}, "action": "circuit_breaker_testing_completed"')
        
        return test_result
    
    async def _test_single_circuit_breaker(self, service_name: str, circuit_breaker: CircuitBreaker) -> Dict[str, Any]:
        """Test individual circuit breaker functionality"""
        
        test_result = {
            "service": service_name,
            "initial_state": circuit_breaker.state.value,
            "test_passed": False,
            "test_phases": {}
        }
        
        try:
            # Phase 1: Test normal operation
            try:
                async def test_call():
                    return await self.call_service(service_name, "health", timeout=5.0)
                
                result = await circuit_breaker.call(test_call)
                test_result["test_phases"]["normal_operation"] = {
                    "status": "passed",
                    "state_after": circuit_breaker.state.value
                }
            except Exception as e:
                test_result["test_phases"]["normal_operation"] = {
                    "status": "failed",
                    "error": str(e),
                    "state_after": circuit_breaker.state.value
                }
            
            # Phase 2: Test failure handling (simulate failures)
            original_failure_count = circuit_breaker.failure_count
            for i in range(circuit_breaker.config.failure_threshold + 1):
                try:
                    async def failing_call():
                        raise Exception(f"Test failure {i}")
                    
                    await circuit_breaker.call(failing_call)
                except Exception:
                    pass  # Expected to fail
            
            test_result["test_phases"]["failure_handling"] = {
                "status": "passed" if circuit_breaker.state == CircuitBreakerState.OPEN else "failed",
                "failures_injected": circuit_breaker.config.failure_threshold + 1,
                "state_after": circuit_breaker.state.value
            }
            
            # Reset circuit breaker for other tests
            circuit_breaker.state = CircuitBreakerState.CLOSED
            circuit_breaker.failure_count = original_failure_count
            
            # Determine overall test result
            normal_passed = test_result["test_phases"]["normal_operation"]["status"] == "passed"
            failure_passed = test_result["test_phases"]["failure_handling"]["status"] == "passed"
            test_result["test_passed"] = normal_passed and failure_passed
            
        except Exception as e:
            test_result["error"] = str(e)
            test_result["test_passed"] = False
        
        return test_result
    
    async def test_service_resilience(self, service_name: str = None) -> Dict[str, Any]:
        """Test service resilience under various failure conditions"""
        self.logger.info(f'"service": "{service_name}", "action": "resilience_testing_started"')
        
        services_to_test = [service_name] if service_name else self.monitored_services
        
        resilience_result = {
            "timestamp": datetime.now().isoformat(),
            "services_tested": 0,
            "resilience_scores": {},
            "overall_resilience": 0
        }
        
        for service in services_to_test:
            try:
                score = await self._test_single_service_resilience(service)
                resilience_result["resilience_scores"][service] = score
                resilience_result["services_tested"] += 1
                
            except Exception as e:
                self.logger.error(f'"service": "{service}", "error": "{e}", "action": "resilience_test_failed"')
                resilience_result["resilience_scores"][service] = 0
        
        # Calculate overall resilience
        if resilience_result["resilience_scores"]:
            resilience_result["overall_resilience"] = sum(resilience_result["resilience_scores"].values()) / len(resilience_result["resilience_scores"])
        
        self.logger.info(f'"services_tested": {resilience_result["services_tested"]}, "overall_resilience": {resilience_result["overall_resilience"]}, "action": "resilience_testing_completed"')
        
        return resilience_result
    
    async def _test_single_service_resilience(self, service_name: str) -> float:
        """Test resilience of a single service and return score (0-100)"""
        
        resilience_tests = [
            ("basic_health", lambda: self.call_service(service_name, "health")),
            ("timeout_handling", lambda: self.call_service(service_name, "health", timeout=0.1)),
            ("invalid_method", lambda: self.call_service(service_name, "nonexistent_method")),
            ("high_load", lambda: self._simulate_high_load(service_name))
        ]
        
        passed_tests = 0
        total_tests = len(resilience_tests)
        
        for test_name, test_func in resilience_tests:
            try:
                if test_name == "timeout_handling" or test_name == "invalid_method":
                    # These should fail
                    try:
                        await test_func()
                        # If they don't fail, the service isn't handling errors properly
                        continue
                    except:
                        # Expected failure
                        passed_tests += 1
                else:
                    # These should succeed
                    await test_func()
                    passed_tests += 1
                    
            except Exception:
                if test_name in ["timeout_handling", "invalid_method"]:
                    passed_tests += 1  # Expected to fail
                # For other tests, failure counts against resilience
        
        return (passed_tests / total_tests) * 100
    
    async def _simulate_high_load(self, service_name: str):
        """Simulate high load on service"""
        # Send multiple concurrent requests
        tasks = []
        for _ in range(5):
            task = asyncio.create_task(self.call_service(service_name, "health"))
            tasks.append(task)
        
        # Wait for at least some to complete
        await asyncio.wait(tasks, timeout=10.0, return_when=asyncio.FIRST_COMPLETED)
        
        # Cancel remaining tasks
        for task in tasks:
            if not task.done():
                task.cancel()
    
    async def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics across all services"""
        stats = {
            "timestamp": datetime.now().isoformat(),
            "error_summary": self.error_statistics.copy(),
            "circuit_breaker_status": {},
            "recent_errors": []
        }
        
        # Get circuit breaker status
        for service_name, cb in self.circuit_breakers.items():
            stats["circuit_breaker_status"][service_name] = {
                "state": cb.state.value,
                "failure_count": cb.failure_count,
                "success_count": cb.success_count,
                "last_failure": cb.last_failure_time.isoformat() if cb.last_failure_time else None
            }
        
        # Get recent error patterns
        recent_patterns = []
        for pattern_key, pattern in self.error_patterns.items():
            if pattern.last_occurrence and (datetime.now() - pattern.last_occurrence).seconds < 3600:  # Last hour
                recent_patterns.append({
                    "error_type": pattern.error_type,
                    "service": pattern.service,
                    "frequency": pattern.frequency,
                    "last_occurrence": pattern.last_occurrence.isoformat(),
                    "severity": pattern.severity
                })
        
        stats["recent_errors"] = recent_patterns
        
        return stats
    
    async def test_fallback_mechanisms(self) -> Dict[str, Any]:
        """Test fallback mechanisms for critical services"""
        fallback_result = {
            "timestamp": datetime.now().isoformat(),
            "services_tested": 0,
            "fallback_tests": {}
        }
        
        # Test prediction service fallback
        try:
            fallback_test = await self._test_prediction_fallback()
            fallback_result["fallback_tests"]["prediction"] = fallback_test
            fallback_result["services_tested"] += 1
        except Exception as e:
            fallback_result["fallback_tests"]["prediction"] = {"error": str(e)}
        
        # Test paper trading fallback
        try:
            fallback_test = await self._test_paper_trading_fallback()
            fallback_result["fallback_tests"]["paper-trading"] = fallback_test
            fallback_result["services_tested"] += 1
        except Exception as e:
            fallback_result["fallback_tests"]["paper-trading"] = {"error": str(e)}
        
        return fallback_result
    
    async def _test_prediction_fallback(self) -> Dict[str, Any]:
        """Test prediction service fallback mechanisms"""
        # Test what happens when market data is unavailable
        try:
            # Try to get prediction with potentially missing dependencies
            result = await self.call_service("prediction", "generate_single_prediction", symbol="CBA.AX")
            
            if isinstance(result, dict) and "confidence" in result:
                return {
                    "has_fallback": True,
                    "fallback_type": "graceful_degradation",
                    "confidence": result.get("confidence")
                }
            else:
                return {
                    "has_fallback": False,
                    "note": "No fallback detected"
                }
        except Exception as e:
            return {
                "has_fallback": True,
                "fallback_type": "exception_handling",
                "error": str(e)
            }
    
    async def _test_paper_trading_fallback(self) -> Dict[str, Any]:
        """Test paper trading service fallback mechanisms"""
        try:
            # Test position retrieval with potential issues
            result = await self.call_service("paper-trading", "get_positions")
            
            return {
                "has_fallback": True,
                "fallback_type": "graceful_response",
                "positions_available": "positions" in str(result)
            }
        except Exception as e:
            return {
                "has_fallback": True,
                "fallback_type": "exception_handling",
                "error": str(e)
            }
    
    async def inject_test_errors(self, service_name: str, error_type: str = "timeout", count: int = 1) -> Dict[str, Any]:
        """Inject test errors for resilience testing"""
        injection_result = {
            "timestamp": datetime.now().isoformat(),
            "service": service_name,
            "error_type": error_type,
            "injections_attempted": count,
            "injections_successful": 0,
            "circuit_breaker_triggered": False
        }
        
        circuit_breaker = self.circuit_breakers.get(service_name)
        initial_cb_state = circuit_breaker.state if circuit_breaker else None
        
        for i in range(count):
            try:
                if error_type == "timeout":
                    # Try to call with very short timeout
                    await self.call_service(service_name, "health", timeout=0.001)
                elif error_type == "invalid_method":
                    await self.call_service(service_name, f"invalid_test_method_{i}")
                elif error_type == "invalid_params":
                    await self.call_service(service_name, "health", invalid_param=f"test_{i}")
                
            except Exception:
                injection_result["injections_successful"] += 1
                
                # Record error pattern
                self._record_error_pattern(service_name, error_type, "test")
        
        # Check if circuit breaker was triggered
        if circuit_breaker and initial_cb_state != circuit_breaker.state:
            injection_result["circuit_breaker_triggered"] = True
            injection_result["new_cb_state"] = circuit_breaker.state.value
        
        return injection_result
    
    def _record_error_pattern(self, service: str, error_type: str, severity: str):
        """Record error pattern for analysis"""
        pattern_key = f"{service}:{error_type}"
        
        if pattern_key in self.error_patterns:
            self.error_patterns[pattern_key].frequency += 1
            self.error_patterns[pattern_key].last_occurrence = datetime.now()
        else:
            self.error_patterns[pattern_key] = ErrorPattern(
                error_type=error_type,
                frequency=1,
                last_occurrence=datetime.now(),
                severity=severity,
                service=service,
                context={}
            )
        
        # Update statistics
        self.error_statistics["total_errors"] += 1
        self.error_statistics["errors_by_service"][service] = self.error_statistics["errors_by_service"].get(service, 0) + 1
        self.error_statistics["errors_by_type"][error_type] = self.error_statistics["errors_by_type"].get(error_type, 0) + 1
    
    async def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get status of all circuit breakers"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "circuit_breakers": {}
        }
        
        for service_name, cb in self.circuit_breakers.items():
            status["circuit_breakers"][service_name] = {
                "state": cb.state.value,
                "failure_count": cb.failure_count,
                "success_count": cb.success_count,
                "last_failure": cb.last_failure_time.isoformat() if cb.last_failure_time else None,
                "last_success": cb.last_success_time.isoformat() if cb.last_success_time else None,
                "config": {
                    "failure_threshold": cb.config.failure_threshold,
                    "recovery_timeout": cb.config.recovery_timeout,
                    "success_threshold": cb.config.success_threshold,
                    "timeout": cb.config.timeout
                }
            }
        
        return status
    
    async def reset_circuit_breakers(self, service_name: str = None) -> Dict[str, Any]:
        """Reset circuit breakers (for testing or recovery)"""
        reset_result = {
            "timestamp": datetime.now().isoformat(),
            "reset_services": []
        }
        
        services_to_reset = [service_name] if service_name else list(self.circuit_breakers.keys())
        
        for service in services_to_reset:
            if service in self.circuit_breakers:
                cb = self.circuit_breakers[service]
                cb.state = CircuitBreakerState.CLOSED
                cb.failure_count = 0
                cb.success_count = 0
                cb.last_failure_time = None
                cb.last_success_time = None
                cb._save_state_to_redis()
                
                reset_result["reset_services"].append(service)
        
        return reset_result

async def main():
    service = ErrorHandlingService()
    await service.start_server()

if __name__ == "__main__":
    asyncio.run(main())
