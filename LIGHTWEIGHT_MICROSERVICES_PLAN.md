# Lightweight VM-Native Microservices Migration Plan

## Executive Summary

**Problem**: Docker's memory overhead (typically 100-200MB per container + orchestration) is prohibitive on a resource-constrained VM.

**Solution**: Native Linux processes with systemd management, Unix domain sockets, and shared memory - achieving microservices benefits with <20MB overhead per service.

**Memory Comparison**:
- Docker approach: ~1.5-2GB overhead for full stack
- Native approach: ~100-200MB total overhead
- Current monolith: Baseline memory usage

## Architecture: Process-Based Microservices

### Core Concept
Each "service" is a **long-running Python process** managed by systemd, communicating via:
- **Unix Domain Sockets** (faster than TCP, zero network overhead)
- **Redis** (single instance, ~50MB RAM for message passing)
- **Shared SQLite databases** (with proper locking)

```
┌─────────────────────────────────────────┐
│                   VM                    │
├─────────────────┬───────────────────────┤
│   systemd       │   Service Processes   │
│   ├─prediction  │   ├─ prediction.py    │
│   ├─market-data │   ├─ market_data.py   │
│   ├─sentiment   │   ├─ sentiment.py     │
│   ├─ml-training │   ├─ ml_training.py   │
│   └─scheduler   │   └─ scheduler.py     │
├─────────────────┴───────────────────────┤
│   IPC Layer: Unix Sockets + Redis      │
├─────────────────────────────────────────┤
│   Data Layer: SQLite + File System     │
└─────────────────────────────────────────┘
```

## Implementation Strategy

### 1. Service Process Structure

```python
# services/base_service.py
import asyncio
import socket
import json
import logging
import signal
import sys
from pathlib import Path
from typing import Dict, Any, Callable
import redis

class BaseService:
    def __init__(self, service_name: str, socket_path: str = None):
        self.service_name = service_name
        self.socket_path = socket_path or f"/tmp/trading_{service_name}.sock"
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.running = True
        self.handlers: Dict[str, Callable] = {}
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format=f'[{service_name}] %(asctime)s %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler(f'/var/log/trading/{service_name}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(service_name)
        
        # Signal handling for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        self.logger.info(f"Received signal {signum}, shutting down gracefully")
        self.running = False
    
    def register_handler(self, method: str, handler: Callable):
        """Register RPC method handler"""
        self.handlers[method] = handler
    
    async def start_server(self):
        """Start Unix socket server"""
        # Remove existing socket
        Path(self.socket_path).unlink(missing_ok=True)
        
        server = await asyncio.start_unix_server(
            self._handle_connection, 
            self.socket_path
        )
        
        # Set socket permissions
        Path(self.socket_path).chmod(0o666)
        
        self.logger.info(f"Service {self.service_name} listening on {self.socket_path}")
        
        async with server:
            await server.serve_forever()
    
    async def _handle_connection(self, reader, writer):
        """Handle incoming socket connection"""
        try:
            data = await reader.read(8192)
            request = json.loads(data.decode())
            
            method = request.get('method')
            params = request.get('params', {})
            
            if method in self.handlers:
                result = await self.handlers[method](**params)
                response = {'status': 'success', 'result': result}
            else:
                response = {'status': 'error', 'error': f'Unknown method: {method}'}
            
            writer.write(json.dumps(response).encode())
            await writer.drain()
            
        except Exception as e:
            error_response = {'status': 'error', 'error': str(e)}
            writer.write(json.dumps(error_response).encode())
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def call_service(self, service_name: str, method: str, **params):
        """Call another service via Unix socket"""
        socket_path = f"/tmp/trading_{service_name}.sock"
        
        try:
            reader, writer = await asyncio.open_unix_connection(socket_path)
            
            request = {
                'method': method,
                'params': params
            }
            
            writer.write(json.dumps(request).encode())
            await writer.drain()
            
            response_data = await reader.read(8192)
            response = json.loads(response_data.decode())
            
            writer.close()
            await writer.wait_closed()
            
            if response['status'] == 'success':
                return response['result']
            else:
                raise Exception(f"Service call failed: {response['error']}")
                
        except Exception as e:
            self.logger.error(f"Failed to call {service_name}.{method}: {e}")
            raise
    
    def publish_event(self, event_type: str, data: dict):
        """Publish event via Redis"""
        try:
            self.redis_client.publish(f"trading:{event_type}", json.dumps(data))
        except Exception as e:
            self.logger.error(f"Failed to publish event {event_type}: {e}")
    
    def subscribe_to_events(self, event_types: list, handler: Callable):
        """Subscribe to events via Redis"""
        pubsub = self.redis_client.pubsub()
        for event_type in event_types:
            pubsub.subscribe(f"trading:{event_type}")
        
        async def event_listener():
            while self.running:
                try:
                    message = pubsub.get_message(timeout=1.0)
                    if message and message['type'] == 'message':
                        event_data = json.loads(message['data'])
                        await handler(message['channel'].decode().split(':')[1], event_data)
                except Exception as e:
                    self.logger.error(f"Event handling error: {e}")
        
        return event_listener
```

### 2. Specific Service Implementations

```python
# services/prediction_service.py
#!/usr/bin/env python3
import asyncio
from base_service import BaseService
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_efficient_system_market_aware import EnhancedMarketAwarePredictor

class PredictionService(BaseService):
    def __init__(self):
        super().__init__("prediction")
        self.predictor = EnhancedMarketAwarePredictor()
        
        # Register RPC methods
        self.register_handler("generate_predictions", self.generate_predictions)
        self.register_handler("get_prediction", self.get_prediction)
        self.register_handler("health_check", self.health_check)
    
    async def generate_predictions(self, symbols: list = None):
        """Generate predictions for symbols"""
        if not symbols:
            symbols = ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX", "MQG.AX", "COL.AX", "BHP.AX"]
        
        predictions = {}
        
        for symbol in symbols:
            try:
                # Get market data from market data service
                market_data = await self.call_service("market-data", "get_market_data", symbol=symbol)
                
                # Get sentiment from sentiment service  
                sentiment_data = await self.call_service("sentiment", "analyze_sentiment", symbol=symbol)
                
                # Generate prediction using existing logic
                prediction = self.predictor.calculate_confidence(
                    symbol=symbol,
                    tech_data=market_data.get("technical", {}),
                    news_data=sentiment_data,
                    volume_data=market_data.get("volume", {}),
                    market_data=market_data.get("market_context", {})
                )
                
                predictions[symbol] = prediction
                
                # Publish prediction event
                self.publish_event("prediction_generated", {
                    "symbol": symbol,
                    "prediction": prediction
                })
                
                self.logger.info(f"Generated prediction for {symbol}: {prediction['action']}")
                
            except Exception as e:
                self.logger.error(f"Failed to generate prediction for {symbol}: {e}")
                predictions[symbol] = {"error": str(e)}
        
        return predictions
    
    async def get_prediction(self, symbol: str):
        """Get latest prediction for symbol"""
        # Query from database service
        return await self.call_service("database", "get_latest_prediction", symbol=symbol)
    
    async def health_check(self):
        """Health check endpoint"""
        return {
            "service": "prediction",
            "status": "healthy",
            "predictor_loaded": self.predictor is not None
        }

async def main():
    service = PredictionService()
    await service.start_server()

if __name__ == "__main__":
    asyncio.run(main())
```

```python
# services/market_data_service.py
#!/usr/bin/env python3
import asyncio
import yfinance as yf
from base_service import BaseService
import time
from datetime import datetime, timedelta

class MarketDataService(BaseService):
    def __init__(self):
        super().__init__("market-data")
        self.cache = {}  # In-memory cache
        self.cache_ttl = 300  # 5 minutes
        
        self.register_handler("get_market_data", self.get_market_data)
        self.register_handler("bulk_fetch", self.bulk_fetch)
        self.register_handler("health_check", self.health_check)
    
    async def get_market_data(self, symbol: str):
        """Get market data for symbol with caching"""
        cache_key = f"market_data:{symbol}"
        
        # Check cache first
        if cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return data
        
        try:
            # Fetch from Yahoo Finance
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d", interval="1h")
            info = ticker.info
            
            market_data = {
                "symbol": symbol,
                "technical": {
                    "current_price": float(hist["Close"].iloc[-1]),
                    "rsi": self._calculate_rsi(hist["Close"]),
                    "macd_histogram": self._calculate_macd(hist["Close"]),
                    "price_vs_sma20": self._calculate_sma_ratio(hist["Close"], 20),
                    "tech_score": self._calculate_tech_score(hist),
                    "market_price": float(hist["Close"].iloc[-1])
                },
                "volume": {
                    "volume_trend": self._calculate_volume_trend(hist["Volume"]),
                    "price_volume_correlation": self._calculate_correlation(hist["Close"], hist["Volume"]),
                    "volume_quality_score": self._calculate_volume_quality(hist["Volume"])
                },
                "market_context": await self._get_market_context()
            }
            
            # Cache the result
            self.cache[cache_key] = (market_data, time.time())
            
            return market_data
            
        except Exception as e:
            self.logger.error(f"Failed to fetch market data for {symbol}: {e}")
            raise
    
    async def bulk_fetch(self, symbols: list):
        """Fetch market data for multiple symbols"""
        results = {}
        for symbol in symbols:
            try:
                results[symbol] = await self.get_market_data(symbol)
            except Exception as e:
                results[symbol] = {"error": str(e)}
        return results
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI - simplified version"""
        deltas = prices.diff()
        gains = deltas.where(deltas > 0, 0).rolling(window=period).mean()
        losses = (-deltas.where(deltas < 0, 0)).rolling(window=period).mean()
        rs = gains / losses
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1]) if not rsi.empty else 50.0
    
    def _calculate_volume_trend(self, volumes):
        """Calculate volume trend percentage"""
        if len(volumes) < 5:
            return 0.0
        recent_avg = volumes.tail(5).mean()
        older_avg = volumes.head(len(volumes)-5).mean()
        return float((recent_avg - older_avg) / older_avg) if older_avg > 0 else 0.0
    
    async def _get_market_context(self):
        """Get ASX 200 market context"""
        try:
            asx200 = yf.Ticker("^AXJO")
            data = asx200.history(period="5d")
            
            if len(data) < 2:
                return {
                    "context": "NEUTRAL",
                    "trend_pct": 0.0,
                    "confidence_multiplier": 1.0,
                    "buy_threshold": 0.70
                }
            
            market_trend = ((data['Close'].iloc[-1] / data['Close'].iloc[0]) - 1) * 100
            
            # Enhanced market context logic from fixes
            if market_trend < -1.5:
                context = "BEARISH"
                confidence_multiplier = 0.7
                buy_threshold = 0.80
            elif market_trend > 1.5:
                context = "BULLISH"
                confidence_multiplier = 1.1
                buy_threshold = 0.65
            elif market_trend < -0.5:
                context = "WEAK_BEARISH"
                confidence_multiplier = 0.9
                buy_threshold = 0.75
            elif market_trend > 0.5:
                context = "WEAK_BULLISH"
                confidence_multiplier = 1.05
                buy_threshold = 0.68
            else:
                context = "NEUTRAL"
                confidence_multiplier = 1.0
                buy_threshold = 0.70
            
            return {
                "context": context,
                "trend_pct": float(market_trend),
                "confidence_multiplier": float(confidence_multiplier),
                "buy_threshold": float(buy_threshold)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get market context: {e}")
            return {
                "context": "NEUTRAL",
                "trend_pct": 0.0,
                "confidence_multiplier": 1.0,
                "buy_threshold": 0.70
            }
    
    async def health_check(self):
        return {
            "service": "market-data",
            "status": "healthy",
            "cache_size": len(self.cache)
        }

async def main():
    service = MarketDataService()
    await service.start_server()

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. Systemd Service Management

```ini
# /etc/systemd/system/trading-prediction.service
[Unit]
Description=Trading Prediction Service
After=network.target redis.service
Requires=redis.service

[Service]
Type=simple
User=trading
Group=trading
WorkingDirectory=/root/test
Environment=PYTHONPATH=/root/test
ExecStart=/root/trading_venv/bin/python services/prediction_service.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Resource limits
MemoryMax=256M
CPUQuota=50%

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/trading-market-data.service
[Unit]
Description=Trading Market Data Service  
After=network.target redis.service
Requires=redis.service

[Service]
Type=simple
User=trading
Group=trading
WorkingDirectory=/root/test
Environment=PYTHONPATH=/root/test
ExecStart=/root/trading_venv/bin/python services/market_data_service.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
MemoryMax=128M
CPUQuota=25%

[Install]
WantedBy=multi-user.target
```

### 4. Service Management Scripts

```bash
#!/bin/bash
# scripts/manage_services.sh

SERVICES=("trading-prediction" "trading-market-data" "trading-sentiment" "trading-scheduler")

case "$1" in
    start)
        echo "Starting trading services..."
        for service in "${SERVICES[@]}"; do
            sudo systemctl start "$service"
            echo "Started $service"
        done
        ;;
    stop)
        echo "Stopping trading services..."
        for service in "${SERVICES[@]}"; do
            sudo systemctl stop "$service"
            echo "Stopped $service"
        done
        ;;
    restart)
        echo "Restarting trading services..."
        for service in "${SERVICES[@]}"; do
            sudo systemctl restart "$service"
            echo "Restarted $service"
        done
        ;;
    status)
        echo "Service status:"
        for service in "${SERVICES[@]}"; do
            status=$(systemctl is-active "$service")
            echo "$service: $status"
        done
        ;;
    logs)
        service=${2:-trading-prediction}
        sudo journalctl -u "$service" -f
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs [service-name]}"
        exit 1
        ;;
esac
```

### 5. Backward Compatibility Layer

```python
# compatibility/service_proxy.py
"""
Drop-in replacement functions that proxy to microservices
Allows existing cron jobs to work unchanged
"""
import asyncio
import json
import socket
import sys

class ServiceProxy:
    def __init__(self):
        self.services_available = self._check_services()
        
    def _check_services(self):
        """Check which services are available"""
        services = ["prediction", "market-data", "sentiment"]
        available = {}
        
        for service in services:
            socket_path = f"/tmp/trading_{service}.sock"
            try:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.connect(socket_path)
                sock.close()
                available[service] = True
            except:
                available[service] = False
                
        return available
    
    async def _call_service(self, service_name: str, method: str, **params):
        """Call service via Unix socket"""
        if not self.services_available.get(service_name):
            raise Exception(f"Service {service_name} not available")
            
        socket_path = f"/tmp/trading_{service_name}.sock"
        
        reader, writer = await asyncio.open_unix_connection(socket_path)
        
        request = {'method': method, 'params': params}
        writer.write(json.dumps(request).encode())
        await writer.drain()
        
        response_data = await reader.read(8192)
        response = json.loads(response_data.decode())
        
        writer.close()
        await writer.wait_closed()
        
        if response['status'] == 'success':
            return response['result']
        else:
            raise Exception(response['error'])

# Global proxy instance
proxy = ServiceProxy()

# Drop-in replacement functions for existing code
def run_enhanced_system():
    """Replace the main() call in enhanced_efficient_system_market_aware.py"""
    try:
        # Try microservices first
        if proxy.services_available.get("prediction"):
            return asyncio.run(proxy._call_service("prediction", "generate_predictions"))
        else:
            # Fallback to original monolithic code
            import enhanced_efficient_system_market_aware
            return enhanced_efficient_system_market_aware.main()
    except Exception as e:
        print(f"Service call failed, falling back to monolithic: {e}")
        import enhanced_efficient_system_market_aware
        return enhanced_efficient_system_market_aware.main()

# Integration in existing cron scripts
if __name__ == "__main__":
    result = run_enhanced_system()
    print(f"Predictions generated: {len(result) if result else 0}")
```

### 6. Modified Cron Job (Minimal Change)

```bash
# Updated cron entry - only change the Python file
*/30 0-5 * * 1-5 cd /root/test && /root/trading_venv/bin/python compatibility/run_predictions.py >> logs/prediction_microservices.log 2>&1
```

```python
# compatibility/run_predictions.py
#!/usr/bin/env python3
"""
Microservices-aware cron entry point
Falls back to monolithic if services unavailable
"""
from service_proxy import run_enhanced_system

if __name__ == "__main__":
    try:
        result = run_enhanced_system()
        print("✅ Predictions completed successfully")
    except Exception as e:
        print(f"❌ Prediction generation failed: {e}")
        exit(1)
```

## Resource Usage Comparison

### Memory Usage Analysis:
```
Docker Approach:
- Base containers: 8 × 100MB = 800MB
- Docker daemon: 200MB  
- Orchestration: 100MB
- Total: ~1.1GB overhead

Native Process Approach:
- Base Python processes: 8 × 15MB = 120MB
- Redis: 50MB
- systemd overhead: ~10MB
- Total: ~180MB overhead

Savings: ~900MB (85% less memory usage)
```

### CPU Usage:
- **Docker**: Container overhead + network virtualization
- **Native**: Direct system calls, Unix socket communication (faster than TCP)

## Migration Path

### Phase 1: Infrastructure Setup (1 week)
```bash
# Install Redis (lightweight message bus)
sudo apt install redis-server
sudo systemctl enable redis-server

# Create service directories
sudo mkdir -p /var/log/trading
sudo mkdir -p /tmp/trading_sockets
sudo chown trading:trading /var/log/trading /tmp/trading_sockets

# Setup systemd services
sudo cp services/*.service /etc/systemd/system/
sudo systemctl daemon-reload
```

### Phase 2: Deploy Services (1 week)
```bash
# Deploy services one by one
sudo systemctl enable trading-market-data
sudo systemctl start trading-market-data

sudo systemctl enable trading-prediction  
sudo systemctl start trading-prediction

# Test services
python -c "
import asyncio
from compatibility.service_proxy import proxy
async def test():
    result = await proxy._call_service('market-data', 'health_check')
    print('Health check:', result)
asyncio.run(test())
"
```

### Phase 3: Switch Cron Jobs (1 week)
```bash
# Update crontab to use compatibility layer
*/30 0-5 * * 1-5 cd /root/test && /root/trading_venv/bin/python compatibility/run_predictions.py >> logs/prediction_microservices.log 2>&1

# Keep old cron as backup (commented out)
# */30 0-5 * * 1-5 cd /root/test && /root/trading_venv/bin/python production/cron/fixed_price_mapping_system.py >> logs/prediction_fixed.log 2>&1
```

## Benefits Over Docker

1. **Memory Efficiency**: 85% less overhead
2. **Speed**: Unix sockets are faster than Docker networking
3. **Simplicity**: Standard Linux tools (systemd, journalctl)
4. **Debugging**: Direct process access, familiar logging
5. **Resource Control**: systemd cgroups for limits
6. **No New Dependencies**: Uses existing Linux infrastructure

This approach gives you **90% of microservices benefits** with **minimal resource overhead** - perfect for your VM constraints while maintaining the reliability and maintainability improvements you're seeking.

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Design lightweight VM-native microservices architecture", "status": "completed", "activeForm": "Designing lightweight VM-native microservices"}, {"content": "Create systemd service management plan", "status": "completed", "activeForm": "Creating systemd service management plan"}, {"content": "Design process-based service isolation", "status": "completed", "activeForm": "Designing process-based service isolation"}, {"content": "Plan lightweight message passing", "status": "completed", "activeForm": "Planning lightweight message passing"}, {"content": "Create VM resource optimization strategy", "status": "completed", "activeForm": "Creating VM resource optimization strategy"}]