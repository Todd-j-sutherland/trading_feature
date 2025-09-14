#!/usr/bin/env python3
"""
Standardized Error Handling Framework for Trading Microservices

This module provides consistent error handling, validation, retry logic,
and recovery strategies across all trading microservices.

Key Features:
- Standardized error response formats
- Comprehensive input validation
- Configurable retry strategies with exponential backoff
- Circuit breaker patterns for external dependencies
- Database error handling with lock retry logic
- Graceful degradation strategies
- Structured error logging with context

Usage:
    from services.common.error_framework import (
        StandardErrorHandler, RetryStrategy, ServiceInputValidator
    )
    
    # In your service
    error_handler = StandardErrorHandler(service_name="prediction")
    
    @error_handler.handle_errors
    async def your_method(self, symbol: str):
        ServiceInputValidator.validate_symbol(symbol)
        # Your logic here

Purpose:
Provides enterprise-grade error handling suitable for financial trading
operations, ensuring consistency, reliability, and proper audit trails.
"""

import asyncio
import json
import logging
import random
import re
import sqlite3
import time
import traceback
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import uuid

# Custom Exception Hierarchy
class TradingError(Exception):
    """Base exception for trading microservices"""
    
    def __init__(self, message: str, error_code: str = None, context: dict = None, recoverable: bool = False):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}
        self.recoverable = recoverable
        self.timestamp = datetime.now().isoformat()

class ValidationError(TradingError):
    """Raised when input validation fails"""
    def __init__(self, message: str, field: str = None, value: Any = None):
        super().__init__(message, "VALIDATION_ERROR", {"field": field, "value": str(value)}, False)

class DataError(TradingError):
    """Raised when data is unavailable or corrupted"""
    def __init__(self, message: str, source: str = None):
        super().__init__(message, "DATA_ERROR", {"source": source}, True)

class APIError(TradingError):
    """Raised when external API calls fail"""
    def __init__(self, message: str, api_name: str = None, status_code: int = None):
        super().__init__(message, "API_ERROR", {"api_name": api_name, "status_code": status_code}, True)

class DatabaseError(TradingError):
    """Raised when database operations fail"""
    def __init__(self, message: str, operation: str = None):
        super().__init__(message, "DATABASE_ERROR", {"operation": operation}, True)

class SecurityError(TradingError):
    """Raised when security violations occur"""
    def __init__(self, message: str, violation_type: str = None):
        super().__init__(message, "SECURITY_ERROR", {"violation_type": violation_type}, False)

class ServiceError(TradingError):
    """Raised when inter-service communication fails"""
    def __init__(self, message: str, service_name: str = None):
        super().__init__(message, "SERVICE_ERROR", {"service_name": service_name}, True)

class MLError(TradingError):
    """Raised when ML/AI components fail"""
    def __init__(self, message: str, model_name: str = None):
        super().__init__(message, "ML_ERROR", {"model_name": model_name}, True)

class ConfigError(TradingError):
    """Raised when configuration is invalid"""
    def __init__(self, message: str, config_key: str = None):
        super().__init__(message, "CONFIG_ERROR", {"config_key": config_key}, False)

# Standardized Response Formats
class StandardResponseFormat:
    """Standardized response formats for all microservices"""
    
    @staticmethod
    def success(
        result: Any,
        request_id: str = None,
        metadata: dict = None,
        execution_time: float = None
    ) -> dict:
        """Create standardized success response"""
        return {
            'status': 'success',
            'success': True,
            'result': result,
            'metadata': metadata or {},
            'request_id': request_id,
            'timestamp': datetime.now().isoformat(),
            'execution_time': execution_time
        }
    
    @staticmethod
    def error(
        error: Union[Exception, str],
        request_id: str = None,
        context: dict = None,
        recoverable: bool = None
    ) -> dict:
        """Create standardized error response"""
        if isinstance(error, TradingError):
            return {
                'status': 'error',
                'success': False,
                'error': {
                    'type': error.__class__.__name__,
                    'code': error.error_code,
                    'message': error.message,
                    'context': error.context,
                    'recoverable': error.recoverable,
                    'timestamp': error.timestamp
                },
                'request_id': request_id
            }
        else:
            return {
                'status': 'error',
                'success': False,
                'error': {
                    'type': 'UnknownError',
                    'code': 'UNKNOWN_ERROR',
                    'message': str(error),
                    'context': context or {},
                    'recoverable': recoverable if recoverable is not None else False,
                    'timestamp': datetime.now().isoformat()
                },
                'request_id': request_id
            }

# Input Validation Framework
class ServiceInputValidator:
    """Comprehensive input validation for trading services"""
    
    @staticmethod
    def validate_symbol(symbol: str) -> str:
        """Validate and normalize stock symbol"""
        if not symbol or not isinstance(symbol, str):
            raise ValidationError("Symbol must be a non-empty string", "symbol", symbol)
        
        symbol = symbol.strip().upper()
        
        # ASX symbols: 1-6 characters followed by .AX
        if not re.match(r'^[A-Z]{1,6}\.AX$', symbol):
            raise ValidationError("Invalid ASX symbol format. Expected: XXX.AX", "symbol", symbol)
        
        return symbol
    
    @staticmethod
    def validate_timeframe(timeframe: str) -> str:
        """Validate timeframe parameter"""
        if not timeframe or not isinstance(timeframe, str):
            raise ValidationError("Timeframe must be a non-empty string", "timeframe", timeframe)
        
        valid_timeframes = ['1d', '1w', '1m', '3m', '6m', '1y', '2y', '5y']
        timeframe = timeframe.lower()
        
        if timeframe not in valid_timeframes:
            raise ValidationError(
                f"Invalid timeframe. Must be one of: {valid_timeframes}",
                "timeframe", 
                timeframe
            )
        
        return timeframe
    
    @staticmethod
    def validate_confidence_threshold(threshold: Union[int, float]) -> float:
        """Validate confidence threshold"""
        if not isinstance(threshold, (int, float)):
            raise ValidationError("Confidence threshold must be a number", "confidence_threshold", threshold)
        
        if not 0 <= threshold <= 1:
            raise ValidationError("Confidence threshold must be between 0 and 1", "confidence_threshold", threshold)
        
        return float(threshold)
    
    @staticmethod
    def validate_date_range(start_date: str, end_date: str = None) -> Tuple[datetime, datetime]:
        """Validate date range parameters"""
        try:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            raise ValidationError("Invalid start_date format. Use ISO format", "start_date", start_date)
        
        if end_date:
            try:
                end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                raise ValidationError("Invalid end_date format. Use ISO format", "end_date", end_date)
        else:
            end = datetime.now()
        
        if start >= end:
            raise ValidationError("start_date must be before end_date", "date_range", f"{start_date} to {end_date}")
        
        # Limit date range to reasonable bounds (e.g., 5 years)
        max_days = 5 * 365
        if (end - start).days > max_days:
            raise ValidationError(f"Date range cannot exceed {max_days} days", "date_range", f"{start_date} to {end_date}")
        
        return start, end
    
    @staticmethod
    def validate_pagination(limit: int = None, offset: int = None) -> Tuple[int, int]:
        """Validate pagination parameters"""
        if limit is not None:
            if not isinstance(limit, int) or limit <= 0:
                raise ValidationError("Limit must be a positive integer", "limit", limit)
            if limit > 1000:  # Reasonable upper bound
                raise ValidationError("Limit cannot exceed 1000", "limit", limit)
        else:
            limit = 100  # Default
        
        if offset is not None:
            if not isinstance(offset, int) or offset < 0:
                raise ValidationError("Offset must be a non-negative integer", "offset", offset)
        else:
            offset = 0  # Default
        
        return limit, offset
    
    @staticmethod
    def validate_service_params(params: dict, required_fields: List[str], optional_fields: List[str] = None) -> dict:
        """Validate service method parameters"""
        optional_fields = optional_fields or []
        
        # Check required fields
        missing_fields = [field for field in required_fields if field not in params]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {missing_fields}", "required_fields", missing_fields)
        
        # Check for unknown fields
        allowed_fields = set(required_fields + optional_fields)
        unknown_fields = [field for field in params.keys() if field not in allowed_fields]
        if unknown_fields:
            raise ValidationError(f"Unknown fields: {unknown_fields}", "unknown_fields", unknown_fields)
        
        return params

# Retry Strategy Framework
class RetryStrategy:
    """Configurable retry strategy with exponential backoff"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        retriable_exceptions: Tuple = None
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        
        # Default retriable exceptions
        self.retriable_exceptions = retriable_exceptions or (
            APIError, DataError, ServiceError, DatabaseError, ConnectionError, TimeoutError
        )
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic"""
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
                    
            except Exception as e:
                last_exception = e
                
                # Don't retry non-retriable exceptions
                if not isinstance(e, self.retriable_exceptions):
                    raise e
                
                # Don't retry on last attempt
                if attempt == self.max_attempts - 1:
                    break
                
                # Calculate delay with exponential backoff
                delay = min(
                    self.base_delay * (self.backoff_factor ** attempt),
                    self.max_delay
                )
                
                # Add jitter to prevent thundering herd
                if self.jitter:
                    delay *= (0.5 + random.random() * 0.5)
                
                # Log retry attempt
                logging.warning(f"Retry {attempt + 1}/{self.max_attempts} for {func.__name__} after {delay:.2f}s: {e}")
                
                await asyncio.sleep(delay)
        
        # All retries exhausted
        raise last_exception

# Database Error Handling
class DatabaseErrorHandler:
    """Enhanced database error handling with SQLite-specific logic"""
    
    @staticmethod
    async def execute_with_retry(
        operation: Callable,
        operation_name: str = "database_operation",
        max_retries: int = 3,
        base_delay: float = 0.5
    ) -> Any:
        """Execute database operation with intelligent retry logic"""
        for attempt in range(max_retries):
            try:
                if asyncio.iscoroutinefunction(operation):
                    return await operation()
                else:
                    return operation()
                    
            except sqlite3.OperationalError as e:
                error_msg = str(e).lower()
                
                if 'database is locked' in error_msg:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 0.1)
                        logging.warning(f"Database locked during {operation_name}, retry {attempt + 1}/{max_retries} in {delay:.2f}s")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise DatabaseError(f"Database remained locked after {max_retries} attempts", operation_name)
                
                elif 'disk i/o error' in error_msg:
                    raise DatabaseError(f"Disk I/O error during {operation_name}", operation_name)
                
                elif 'database disk image is malformed' in error_msg:
                    raise DatabaseError(f"Database corruption detected during {operation_name}", operation_name)
                
                else:
                    raise DatabaseError(f"SQLite operational error during {operation_name}: {e}", operation_name)
            
            except sqlite3.IntegrityError as e:
                raise DatabaseError(f"Data integrity error during {operation_name}: {e}", operation_name)
            
            except sqlite3.DatabaseError as e:
                raise DatabaseError(f"Database error during {operation_name}: {e}", operation_name)
            
            except Exception as e:
                raise DatabaseError(f"Unexpected error during {operation_name}: {e}", operation_name)

# Circuit Breaker Implementation
class CircuitBreaker:
    """Circuit breaker for external service calls"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise ServiceError("Circuit breaker is OPEN - service unavailable")
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time > self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

# Main Error Handler Class
class StandardErrorHandler:
    """Centralized error handler for trading microservices"""
    
    def __init__(self, service_name: str, logger: logging.Logger = None):
        self.service_name = service_name
        self.logger = logger or logging.getLogger(service_name)
        self.error_counts = {}
        self.circuit_breakers = {}
        self.retry_strategies = {}
    
    def register_circuit_breaker(self, name: str, circuit_breaker: CircuitBreaker):
        """Register a circuit breaker"""
        self.circuit_breakers[name] = circuit_breaker
    
    def register_retry_strategy(self, name: str, retry_strategy: RetryStrategy):
        """Register a retry strategy"""
        self.retry_strategies[name] = retry_strategy
    
    def handle_errors(self, 
                     return_format: str = "standard",
                     log_errors: bool = True,
                     validate_inputs: bool = True):
        """Decorator for comprehensive error handling"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                request_id = str(uuid.uuid4())
                start_time = time.time()
                
                try:
                    # Input validation if requested
                    if validate_inputs and hasattr(func, '_input_validators'):
                        for validator in func._input_validators:
                            validator(*args, **kwargs)
                    
                    # Execute function
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)
                    
                    execution_time = time.time() - start_time
                    
                    # Return success response
                    if return_format == "standard":
                        return StandardResponseFormat.success(
                            result=result,
                            request_id=request_id,
                            execution_time=execution_time
                        )
                    else:
                        return result
                
                except Exception as e:
                    execution_time = time.time() - start_time
                    
                    # Log error if requested
                    if log_errors:
                        self._log_error(e, func.__name__, request_id, execution_time)
                    
                    # Track error frequency
                    error_key = f"{func.__name__}:{type(e).__name__}"
                    self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
                    
                    # Return error response
                    if return_format == "standard":
                        return StandardResponseFormat.error(
                            error=e,
                            request_id=request_id,
                            context={
                                "function": func.__name__,
                                "service": self.service_name,
                                "execution_time": execution_time
                            }
                        )
                    else:
                        raise e
            
            return wrapper
        return decorator
    
    def _log_error(self, error: Exception, function_name: str, request_id: str, execution_time: float):
        """Log error with structured format"""
        error_context = {
            "service": self.service_name,
            "function": function_name,
            "request_id": request_id,
            "execution_time": execution_time,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat()
        }
        
        if isinstance(error, TradingError):
            error_context.update({
                "error_code": error.error_code,
                "error_context": error.context,
                "recoverable": error.recoverable
            })
        
        # Log with appropriate level
        if isinstance(error, (ValidationError, ConfigError)):
            self.logger.warning(f"Validation/Config error: {json.dumps(error_context)}")
        elif isinstance(error, SecurityError):
            self.logger.error(f"Security error: {json.dumps(error_context)}")
        elif isinstance(error, (APIError, DataError, ServiceError)):
            self.logger.warning(f"External service error: {json.dumps(error_context)}")
        else:
            self.logger.error(f"Unexpected error: {json.dumps(error_context)}")
            self.logger.debug(f"Error traceback: {traceback.format_exc()}")
    
    def get_error_statistics(self) -> dict:
        """Get error statistics for monitoring"""
        return {
            "service": self.service_name,
            "error_counts": self.error_counts,
            "circuit_breaker_states": {
                name: cb.state for name, cb in self.circuit_breakers.items()
            },
            "timestamp": datetime.now().isoformat()
        }

# Validation Decorators
def validate_symbol(func: Callable):
    """Decorator to validate symbol parameter"""
    if not hasattr(func, '_input_validators'):
        func._input_validators = []
    
    def validator(*args, **kwargs):
        if 'symbol' in kwargs:
            kwargs['symbol'] = ServiceInputValidator.validate_symbol(kwargs['symbol'])
        elif len(args) > 1:  # Assuming symbol is second parameter after self
            args = list(args)
            args[1] = ServiceInputValidator.validate_symbol(args[1])
            args = tuple(args)
        return args, kwargs
    
    func._input_validators.append(validator)
    return func

def validate_timeframe(func: Callable):
    """Decorator to validate timeframe parameter"""
    if not hasattr(func, '_input_validators'):
        func._input_validators = []
    
    def validator(*args, **kwargs):
        if 'timeframe' in kwargs:
            kwargs['timeframe'] = ServiceInputValidator.validate_timeframe(kwargs['timeframe'])
        return args, kwargs
    
    func._input_validators.append(validator)
    return func

# Export main components
__all__ = [
    # Exceptions
    'TradingError', 'ValidationError', 'DataError', 'APIError', 'DatabaseError',
    'SecurityError', 'ServiceError', 'MLError', 'ConfigError',
    
    # Core Classes
    'StandardErrorHandler', 'StandardResponseFormat', 'ServiceInputValidator',
    'RetryStrategy', 'DatabaseErrorHandler', 'CircuitBreaker',
    
    # Decorators
    'validate_symbol', 'validate_timeframe'
]
