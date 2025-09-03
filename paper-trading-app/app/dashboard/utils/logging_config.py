"""
Dashboard-specific logging configuration and utilities
"""

import logging
import time
import traceback
from functools import wraps
from typing import Any, Callable, Dict, Optional
from pathlib import Path

from app.config.logging import setup_logging, get_logger


def setup_dashboard_logger(
    name: str = "dashboard",
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Setup dashboard-specific logging configuration
    
    Args:
        name: Logger name (usually __name__ of the module)
        level: Logging level (default: INFO)
        log_file: Optional log file path for dashboard logs
        
    Returns:
        Dashboard logger instance
    """
    # Use the centralized logging setup (only if not already setup)
    if not logging.getLogger().handlers:
        if log_file is None:
            log_file = "logs/dashboard.log"
        setup_logging(level=level, log_file=log_file)
    
    # Return dashboard-specific logger
    dashboard_logger = get_logger(name)
    dashboard_logger.info(f"Dashboard logging initialized for {name}")
    
    return dashboard_logger


def log_error_with_context(
    logger: logging.Logger,
    error: Exception,
    context: Any,
    operation: str = "Unknown operation"
) -> None:
    """
    Log error with additional context information
    
    Args:
        logger: Logger instance
        error: Exception that occurred
        context: Additional context information (dict, string, or other)
        operation: Description of the operation that failed
    """
    error_msg = f"Error in {operation}: {str(error)}"
    
    # Handle different context types
    if isinstance(context, dict):
        context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
        if context_str:
            error_msg += f" | Context: {context_str}"
    elif context:
        error_msg += f" | Context: {str(context)}"
    
    # Log the error with traceback
    logger.error(error_msg)
    logger.debug(f"Traceback: {traceback.format_exc()}")


def log_performance_metrics(
    logger: logging.Logger,
    operation: str,
    duration: float,
    metrics: Optional[Any] = None
) -> None:
    """
    Log performance metrics for dashboard operations
    
    Args:
        logger: Logger instance
        operation: Description of the operation
        duration: Time taken in seconds
        metrics: Additional performance metrics (dict or other)
    """
    perf_msg = f"Performance - {operation}: {duration:.3f}s"
    
    if metrics:
        if isinstance(metrics, dict):
            metrics_str = ", ".join([f"{k}={v}" for k, v in metrics.items()])
            perf_msg += f" | Metrics: {metrics_str}"
        else:
            perf_msg += f" | Metrics: {str(metrics)}"
    
    logger.info(perf_msg)


def log_data_loading_stats(
    logger: logging.Logger,
    symbol: str,
    record_count: int,
    file_path: str
) -> None:
    """
    Log data loading statistics
    
    Args:
        logger: Logger instance
        symbol: Stock symbol being loaded
        record_count: Number of records loaded
        file_path: Path to the data file
    """
    stats_msg = f"Data loaded - Symbol: {symbol}, Records: {record_count}, File: {file_path}"
    logger.info(stats_msg)


def performance_monitor(operation: str):
    """
    Decorator to monitor and log performance of dashboard functions
    
    Args:
        operation: Description of the operation being monitored
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger("dashboard.performance")
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                log_performance_metrics(
                    logger=logger,
                    operation=f"{operation} ({func.__name__})",
                    duration=duration
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                log_error_with_context(
                    logger=logger,
                    error=e,
                    context={"duration": duration, "args": len(args), "kwargs": len(kwargs)},
                    operation=f"{operation} ({func.__name__})"
                )
                raise
                
        return wrapper
    return decorator


def dashboard_error_handler(operation: str):
    """
    Decorator to handle and log errors in dashboard functions
    
    Args:
        operation: Description of the operation
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger("dashboard.errors")
            
            try:
                return func(*args, **kwargs)
                
            except Exception as e:
                log_error_with_context(
                    logger=logger,
                    error=e,
                    context={"function": func.__name__, "args": len(args), "kwargs": len(kwargs)},
                    operation=operation
                )
                # Re-raise the exception so Streamlit can handle it appropriately
                raise
                
        return wrapper
    return decorator
