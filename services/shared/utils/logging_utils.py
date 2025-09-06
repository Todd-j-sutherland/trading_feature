"""Logging utilities for trading services"""

import logging
import sys
import os
from typing import Optional
from datetime import datetime
from pathlib import Path


def setup_logging(
    service_name: str,
    log_level: str = "INFO",
    log_dir: Optional[str] = None,
    console_output: bool = True
) -> logging.Logger:
    """Setup logging for a service"""
    
    # Create logger
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_dir:
        # Ensure log directory exists
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        # Create log file path
        log_file = os.path.join(log_dir, f"{service_name}.log")
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Also create error-only log file
        error_log_file = os.path.join(log_dir, f"{service_name}_errors.log")
        error_handler = logging.FileHandler(error_log_file)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)


class ServiceLogger:
    """Enhanced logger for services with structured logging"""
    
    def __init__(self, service_name: str, log_dir: Optional[str] = None):
        self.service_name = service_name
        self.logger = setup_logging(service_name, log_dir=log_dir)
    
    def info(self, message: str, **kwargs):
        """Log info message with context"""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with context"""
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context"""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context"""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """Log message with additional context"""
        context = ""
        if kwargs:
            context_parts = [f"{k}={v}" for k, v in kwargs.items()]
            context = f" | {' | '.join(context_parts)}"
        
        full_message = f"{message}{context}"
        self.logger.log(level, full_message)
    
    def log_request(self, endpoint: str, method: str = "GET", **kwargs):
        """Log API request"""
        self.info(f"API Request: {method} {endpoint}", **kwargs)
    
    def log_response(self, endpoint: str, status: int, duration_ms: float, **kwargs):
        """Log API response"""
        self.info(f"API Response: {endpoint} | Status: {status} | Duration: {duration_ms:.2f}ms", **kwargs)
    
    def log_error_with_traceback(self, message: str, exception: Exception, **kwargs):
        """Log error with traceback"""
        import traceback
        tb = traceback.format_exc()
        self.error(f"{message} | Exception: {str(exception)} | Traceback: {tb}", **kwargs)
    
    def log_performance(self, operation: str, duration_ms: float, **kwargs):
        """Log performance metrics"""
        self.info(f"Performance: {operation} | Duration: {duration_ms:.2f}ms", **kwargs)
    
    def log_health_check(self, component: str, status: str, **kwargs):
        """Log health check results"""
        self.info(f"Health Check: {component} | Status: {status}", **kwargs)


class RequestLogger:
    """Logger for tracking requests and responses"""
    
    def __init__(self, service_name: str):
        self.logger = ServiceLogger(f"{service_name}_requests")
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds() * 1000
            if exc_type:
                self.logger.error(f"Request failed after {duration:.2f}ms", 
                                exception=str(exc_val))
            else:
                self.logger.info(f"Request completed in {duration:.2f}ms")


def log_function_call(func):
    """Decorator to log function calls"""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        
        start_time = datetime.now()
        try:
            result = func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds() * 1000
            logger.debug(f"Function {func.__name__} completed in {duration:.2f}ms")
            return result
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Function {func.__name__} failed after {duration:.2f}ms: {str(e)}")
            raise
    
    return wrapper


# Default log directory - can be overridden
DEFAULT_LOG_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'logs', 'services')


def get_service_logger(service_name: str, log_dir: Optional[str] = None) -> ServiceLogger:
    """Get a service logger instance"""
    if log_dir is None:
        log_dir = DEFAULT_LOG_DIR
    return ServiceLogger(service_name, log_dir)
