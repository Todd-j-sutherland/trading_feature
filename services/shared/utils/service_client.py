"""Service client for inter-service communication"""

import asyncio
import time
from typing import Dict, Any, Optional
from datetime import datetime

try:
    import aiohttp
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    # Fallback imports
    import urllib.request
    import json

try:
    from ..models.trading_models import TradingSignal, TradingRequest
    from ..models.sentiment_models import SentimentScore, SentimentRequest
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False


class ServiceClient:
    """Client for communicating with other services"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = None
        
        if REQUESTS_AVAILABLE:
            self.session = requests.Session()
            self.session.timeout = timeout
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request with fallback handling"""
        url = f"{self.base_url}{endpoint}"
        
        if REQUESTS_AVAILABLE and self.session:
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, timeout=self.timeout)
                elif method.upper() == 'POST':
                    response = self.session.post(url, json=data, timeout=self.timeout)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                response.raise_for_status()
                return response.json()
            except Exception as e:
                raise ConnectionError(f"Failed to connect to {url}: {str(e)}")
        else:
            # Fallback implementation using urllib
            try:
                req_data = None
                headers = {'Content-Type': 'application/json'}
                
                if data:
                    req_data = json.dumps(data).encode('utf-8')
                
                request = urllib.request.Request(url, data=req_data, headers=headers)
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    return json.loads(response.read().decode('utf-8'))
            except Exception as e:
                raise ConnectionError(f"Failed to connect to {url}: {str(e)}")
    
    async def _make_async_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make async HTTP request"""
        if not REQUESTS_AVAILABLE:
            # Fall back to sync request in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._make_request, method, endpoint, data)
        
        url = f"{self.base_url}{endpoint}"
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            try:
                if method.upper() == 'GET':
                    async with session.get(url) as response:
                        response.raise_for_status()
                        return await response.json()
                elif method.upper() == 'POST':
                    async with session.post(url, json=data) as response:
                        response.raise_for_status()
                        return await response.json()
                else:
                    raise ValueError(f"Unsupported method: {method}")
            except Exception as e:
                raise ConnectionError(f"Failed to connect to {url}: {str(e)}")
    
    def health_check(self) -> bool:
        """Check if service is healthy"""
        try:
            response = self._make_request('GET', '/health')
            return response.get('status') == 'healthy'
        except Exception:
            return False
    
    async def async_health_check(self) -> bool:
        """Async health check"""
        try:
            response = await self._make_async_request('GET', '/health')
            return response.get('status') == 'healthy'
        except Exception:
            return False
    
    # Generic HTTP methods
    def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Generic GET request"""
        if kwargs:
            # Add query parameters
            params = "&".join([f"{k}={v}" for k, v in kwargs.items()])
            endpoint += f"?{params}"
        
        return self._make_request('GET', endpoint)
    
    def post(self, endpoint: str, data: Optional[Dict] = None, json: Optional[Dict] = None) -> Dict[str, Any]:
        """Generic POST request"""
        # Support both 'data' and 'json' parameters for compatibility
        payload = data or json
        return self._make_request('POST', endpoint, payload)
    
    # Sentiment service methods
    def get_sentiment(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Get sentiment analysis for a symbol"""
        endpoint = f"/sentiment/{symbol}"
        if kwargs:
            # Add query parameters
            params = "&".join([f"{k}={v}" for k, v in kwargs.items()])
            endpoint += f"?{params}"
        
        return self._make_request('GET', endpoint)
    
    async def async_get_sentiment(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Async get sentiment analysis"""
        endpoint = f"/sentiment/{symbol}"
        if kwargs:
            params = "&".join([f"{k}={v}" for k, v in kwargs.items()])
            endpoint += f"?{params}"
        
        return await self._make_async_request('GET', endpoint)
    
    def analyze_sentiment(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment with custom request"""
        return self._make_request('POST', '/sentiment/analyze', request_data)
    
    # Trading service methods
    def analyze_trading_signal(self, symbol: str, sentiment_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Get trading signal analysis"""
        request_data = {
            'symbol': symbol,
            'sentiment_data': sentiment_data,
            'timestamp': datetime.now().isoformat()
        }
        return self._make_request('POST', '/trading/analyze', request_data)
    
    async def async_analyze_trading_signal(self, symbol: str, sentiment_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Async trading signal analysis"""
        request_data = {
            'symbol': symbol,
            'sentiment_data': sentiment_data,
            'timestamp': datetime.now().isoformat()
        }
        return await self._make_async_request('POST', '/trading/analyze', request_data)
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary"""
        return self._make_request('GET', '/trading/portfolio')
    
    def get_positions(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get current positions"""
        endpoint = '/trading/positions'
        if symbol:
            endpoint += f"?symbol={symbol}"
        return self._make_request('GET', endpoint)
    
    # Orchestrator service methods
    def get_recommendation(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive trading recommendation"""
        return self._make_request('GET', f'/recommendation/{symbol}')
    
    async def async_get_recommendation(self, symbol: str) -> Dict[str, Any]:
        """Async comprehensive trading recommendation"""
        return await self._make_async_request('GET', f'/recommendation/{symbol}')
    
    def get_market_status(self) -> Dict[str, Any]:
        """Get current market status"""
        return self._make_request('GET', '/market/status')
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system-wide health status"""
        return self._make_request('GET', '/system/health')
    
    # Utility methods
    def close(self):
        """Close the session"""
        if self.session:
            self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class ServiceDiscovery:
    """Service discovery helper"""
    
    def __init__(self):
        self.services = {
            'orchestrator': 'http://localhost:8000',
            'trading': 'http://localhost:8001', 
            'sentiment': 'http://localhost:8002',
            'ml': 'http://localhost:8003',  # Future
            'data': 'http://localhost:8004',  # Future
            'dashboard': 'http://localhost:8005',  # Future
        }
        self.health_cache = {}
        self.cache_timeout = 30  # seconds
    
    def get_service_url(self, service_name: str) -> str:
        """Get URL for a service"""
        return self.services.get(service_name)
    
    def get_client(self, service_name: str) -> ServiceClient:
        """Get service client for a service"""
        url = self.get_service_url(service_name)
        if not url:
            raise ValueError(f"Unknown service: {service_name}")
        return ServiceClient(url)
    
    def is_service_healthy(self, service_name: str) -> bool:
        """Check if service is healthy (with caching)"""
        cache_key = f"{service_name}_health"
        current_time = time.time()
        
        # Check cache first
        if cache_key in self.health_cache:
            cached_time, cached_result = self.health_cache[cache_key]
            if current_time - cached_time < self.cache_timeout:
                return cached_result
        
        # Check service health
        try:
            client = self.get_client(service_name)
            is_healthy = client.health_check()
            client.close()
            
            # Cache result
            self.health_cache[cache_key] = (current_time, is_healthy)
            return is_healthy
        except Exception:
            # Cache negative result for shorter time
            self.health_cache[cache_key] = (current_time, False)
            return False
    
    def get_healthy_services(self) -> Dict[str, bool]:
        """Get health status of all services"""
        return {name: self.is_service_healthy(name) for name in self.services.keys()}


# Global service discovery instance
service_discovery = ServiceDiscovery()
