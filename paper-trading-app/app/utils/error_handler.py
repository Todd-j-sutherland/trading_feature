"""
Robust Error Handling System
============================

Centralized error handling for the trading application with:
- Structured error logging
- Graceful degradation
- User-friendly error messages
- Automatic recovery mechanisms
"""

import logging
import traceback
import sys
from typing import Optional, Dict, Any, Callable
from functools import wraps
from datetime import datetime
import json

class TradingError(Exception):
    """Base exception for trading application errors"""
    pass

class DataError(TradingError):
    """Raised when data is unavailable or corrupted"""
    pass

class APIError(TradingError):
    """Raised when external API calls fail"""
    pass

class ConfigError(TradingError):
    """Raised when configuration is invalid"""
    pass

class MLError(TradingError):
    """Raised when ML components fail"""
    pass

class ErrorHandler:
    """Centralized error handling and recovery system"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.error_count = {}
        self.recovery_strategies = {}
        
    def register_recovery_strategy(self, error_type: type, strategy: Callable):
        """Register a recovery strategy for a specific error type"""
        self.recovery_strategies[error_type] = strategy
    
    def handle_error(self, error: Exception, context: str = "", 
                    attempt_recovery: bool = True) -> Dict[str, Any]:
        """
        Handle an error with optional recovery
        
        Returns:
            Dict with 'success', 'error', 'recovery_attempted', 'message' keys
        """
        error_type = type(error)
        error_key = f"{error_type.__name__}:{context}"
        
        # Track error frequency
        self.error_count[error_key] = self.error_count.get(error_key, 0) + 1
        
        # Log the error
        self.logger.error(f"Error in {context}: {error}")
        self.logger.debug(f"Error traceback: {traceback.format_exc()}")
        
        result = {
            'success': False,
            'error': str(error),
            'error_type': error_type.__name__,
            'context': context,
            'recovery_attempted': False,
            'message': self._get_user_friendly_message(error, context),
            'timestamp': datetime.now().isoformat()
        }
        
        # Attempt recovery if strategy exists
        if attempt_recovery and error_type in self.recovery_strategies:
            try:
                recovery_result = self.recovery_strategies[error_type](error, context)
                result['recovery_attempted'] = True
                result['recovery_result'] = recovery_result
                
                if recovery_result.get('success', False):
                    result['success'] = True
                    result['message'] = "Error resolved through automatic recovery"
                    self.logger.info(f"Recovery successful for {error_key}")
                else:
                    self.logger.warning(f"Recovery failed for {error_key}")
                    
            except Exception as recovery_error:
                self.logger.error(f"Recovery strategy failed: {recovery_error}")
                result['recovery_error'] = str(recovery_error)
        
        return result
    
    def _get_user_friendly_message(self, error: Exception, context: str) -> str:
        """Generate user-friendly error messages"""
        error_type = type(error)
        
        if error_type == DataError:
            return "📊 Data temporarily unavailable. The system will retry automatically."
        elif error_type == APIError:
            return "🌐 External service unavailable. Using cached data where possible."
        elif error_type == ConfigError:
            return "⚙️ Configuration issue detected. Please check your settings."
        elif error_type == MLError:
            return "🤖 ML analysis temporarily unavailable. Using traditional analysis."
        elif "timeout" in str(error).lower():
            return "⏰ Operation timed out. This is usually temporary."
        elif "connection" in str(error).lower():
            return "🔌 Connection issue detected. Please check your internet connection."
        else:
            return f"⚠️ An issue occurred in {context}. The system will attempt to continue."

def robust_execution(fallback_value=None, context="operation"):
    """
    Decorator for robust execution with automatic error handling
    
    Usage:
        @robust_execution(fallback_value={}, context="sentiment_analysis")
        def analyze_sentiment(symbol):
            # Your code here
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = ErrorHandler()
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                result = error_handler.handle_error(e, context)
                
                if result['success']:
                    # Recovery was successful, try again
                    try:
                        return func(*args, **kwargs)
                    except Exception as retry_error:
                        # Recovery didn't work, return fallback
                        logging.getLogger(__name__).warning(
                            f"Function {func.__name__} failed after recovery attempt"
                        )
                        return fallback_value
                else:
                    # No recovery possible, return fallback
                    logging.getLogger(__name__).warning(
                        f"Function {func.__name__} failed: {result['message']}"
                    )
                    return fallback_value
        
        return wrapper
    return decorator

def safe_import(module_name: str, fallback=None):
    """Safely import a module with fallback"""
    try:
        return __import__(module_name)
    except ImportError as e:
        logging.getLogger(__name__).warning(f"Failed to import {module_name}: {e}")
        return fallback

def validate_inputs(**validators):
    """
    Decorator for input validation
    
    Usage:
        @validate_inputs(symbol=lambda x: isinstance(x, str) and len(x) > 0)
        def analyze_symbol(symbol):
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature to map args to parameter names
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate inputs
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if not validator(value):
                        raise ValueError(f"Invalid input for parameter '{param_name}': {value}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
