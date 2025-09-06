"""
Shared utilities for trading system services.
"""

import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional
from functools import wraps
import requests
import time


def setup_service_logging(service_name: str, log_level: str = "INFO") -> logging.Logger:
    """Setup standardized logging for a service."""
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(
        f'%(asctime)s - {service_name} - %(levelname)s - %(message)s'
    )
    
    # Create handler
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry function calls on failure."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
            return None
        return wrapper
    return decorator


def health_check_endpoint(service_name: str, version: str = "1.0.0"):
    """Create a standardized health check response."""
    def health_check():
        return {
            "service": service_name,
            "version": version,
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": time.time()
        }
    return health_check


class ServiceClient:
    """Base client for inter-service communication."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
    
    @retry_on_failure(max_retries=3)
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make GET request to service."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()
    
    @retry_on_failure(max_retries=3)
    def post(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make POST request to service."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.post(
            url, 
            json=data, 
            timeout=self.timeout,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        return self.get("/health")


def validate_symbol(symbol: str) -> str:
    """Validate and normalize stock symbol."""
    if not symbol:
        raise ValueError("Symbol cannot be empty")
    
    # Normalize symbol (uppercase, add .AX if needed for ASX stocks)
    symbol = symbol.upper().strip()
    
    # Common ASX bank symbols
    asx_banks = ["CBA", "ANZ", "WBC", "NAB", "MQG", "SUN", "BOQ", "BEN"]
    
    if symbol in asx_banks:
        symbol = f"{symbol}.AX"
    
    return symbol


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert value to int."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class ConfigError(Exception):
    """Configuration related errors."""
    pass


def load_service_config(config_path: str) -> Dict[str, Any]:
    """Load service configuration from file."""
    try:
        with open(config_path, 'r') as f:
            if config_path.endswith('.json'):
                return json.load(f)
            else:
                # Assume it's a simple key=value format
                config = {}
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
                return config
    except Exception as e:
        raise ConfigError(f"Failed to load config from {config_path}: {e}")