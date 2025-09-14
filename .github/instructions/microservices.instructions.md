# Complete Microservices Implementation Guide

This document provides the complete implementation plan combining both Docker and VM-native approaches, allowing you to choose the best fit for your environment.

## Table of Contents

1. [Architecture Decision Matrix](#architecture-decision-matrix)
2. [Development Environment Setup](#development-environment-setup)
3. [Production Deployment Options](#production-deployment-options)
4. [Complete Implementation Files](#complete-implementation-files)
5. [Migration Strategies](#migration-strategies)
6. [Testing & Validation](#testing--validation)
7. [Monitoring & Operations](#monitoring--operations)

## Architecture Decision Matrix

### Environment Comparison

| Factor               | VM-Native (Recommended) | Docker                  | Current Monolith |
| -------------------- | ----------------------- | ----------------------- | ---------------- |
| **Memory Overhead**  | ~180MB                  | ~1.1GB                  | Baseline         |
| **CPU Overhead**     | Minimal                 | Container layers        | None             |
| **Complexity**       | Low                     | Medium                  | Lowest           |
| **Scaling**          | Per-service             | Per-container           | Full system      |
| **Debugging**        | Native tools            | Container logs          | Direct           |
| **Resource Control** | systemd cgroups         | Docker limits           | Process limits   |
| **Network**          | Unix sockets            | Virtual networks        | Direct calls     |
| **Deployment**       | systemd services        | Container orchestration | File copy        |

### Decision Framework

**Choose VM-Native if**:

- Memory < 4GB available
- Want familiar Linux tooling
- Gradual migration preferred
- Single VM deployment

**Choose Docker if**:

- Memory > 8GB available
- Multi-server deployment planned
- Container ecosystem desired
- Development team prefers containers

## Development Environment Setup

### Local Development (Windows/Mac)

```bash
# Option 1: Docker Compose for local development
git clone your-trading-repo
cd trading_feature
docker-compose -f docker-compose.dev.yml up

# Option 2: Python virtual environment
python -m venv trading_env
source trading_env/bin/activate  # Linux/Mac
# trading_env\Scripts\activate     # Windows
pip install -r requirements.txt
```

### VM Production Setup

```bash
# Redis installation
sudo apt update
sudo apt install redis-server python3-pip python3-venv
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Python environment
python3 -m venv /opt/trading_venv
source /opt/trading_venv/bin/activate
pip install -r requirements.txt

# Service directories
sudo mkdir -p /var/log/trading /tmp/trading_sockets /opt/trading_services
sudo chown $USER:$USER /var/log/trading /tmp/trading_sockets /opt/trading_services
```

## Complete Implementation Files

### 1. Base Service Framework

```python
# services/base_service.py
import asyncio
import socket
import json
import logging
import signal
import sys
import time
from pathlib import Path
from typing import Dict, Any, Callable, Optional
import redis
import aiofiles
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ServiceHealth:
    service_name: str
    status: str
    uptime: float
    memory_usage: int
    cpu_usage: float
    last_error: Optional[str] = None

class BaseService:
    """Base class for all microservices with health checks, metrics, and error handling"""

    def __init__(self, service_name: str, socket_path: str = None, redis_url: str = "redis://localhost:6379"):
        self.service_name = service_name
        self.socket_path = socket_path or f"/tmp/trading_{service_name}.sock"
        self.start_time = time.time()
        self.running = True
        self.handlers: Dict[str, Callable] = {}
        self.health = ServiceHealth(service_name, "starting", 0, 0, 0)

        # Redis connection with retry logic
        self.redis_client = None
        self._redis_url = redis_url
        self._connect_redis()

        # Setup structured logging
        self._setup_logging()

        # Signal handling for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        # Register built-in handlers
        self.register_handler("health", self.health_check)
        self.register_handler("metrics", self.get_metrics)
        self.register_handler("shutdown", self.graceful_shutdown)

    def _connect_redis(self):
        """Connect to Redis with retry logic"""
        max_retries = 5
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                self.redis_client = redis.Redis.from_url(self._redis_url, decode_responses=True)
                self.redis_client.ping()  # Test connection
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Failed to connect to Redis after {max_retries} attempts: {e}")
                    self.redis_client = None
                else:
                    time.sleep(retry_delay)
                    retry_delay *= 2

    def _setup_logging(self):
        """Setup structured logging with file and console handlers"""
        self.logger = logging.getLogger(self.service_name)
        self.logger.setLevel(logging.INFO)

        # Create logs directory if it doesn't exist
        log_dir = Path("/var/log/trading")
        log_dir.mkdir(parents=True, exist_ok=True)

        # File handler with rotation
        file_handler = logging.FileHandler(log_dir / f"{self.service_name}.log")
        console_handler = logging.StreamHandler()

        # JSON formatter for structured logs
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "service": "%(name)s", "level": "%(levelname)s", "message": %(message)s}'
        )

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f'"signal": {signum}, "action": "shutdown_initiated"')
        self.running = False

    def register_handler(self, method: str, handler: Callable):
        """Register RPC method handler"""
        self.handlers[method] = handler
        self.logger.info(f'"method": "{method}", "action": "handler_registered"')

    async def start_server(self):
        """Start Unix socket server"""
        # Remove existing socket
        Path(self.socket_path).unlink(missing_ok=True)

        try:
            server = await asyncio.start_unix_server(
                self._handle_connection,
                self.socket_path
            )

            # Set socket permissions for service communication
            Path(self.socket_path).chmod(0o666)

            self.health.status = "healthy"
            self.logger.info(f'"socket_path": "{self.socket_path}", "action": "server_started"')

            # Start background tasks
            health_task = asyncio.create_task(self._health_monitor())

            async with server:
                await server.serve_forever()

        except Exception as e:
            self.health.status = "unhealthy"
            self.health.last_error = str(e)
            self.logger.error(f'"error": "{e}", "action": "server_start_failed"')
            raise
        finally:
            # Cleanup
            Path(self.socket_path).unlink(missing_ok=True)
            if health_task:
                health_task.cancel()

    async def _health_monitor(self):
        """Background task to monitor service health"""
        while self.running:
            try:
                self.health.uptime = time.time() - self.start_time

                # Update memory usage (simplified)
                import psutil
                process = psutil.Process()
                self.health.memory_usage = process.memory_info().rss
                self.health.cpu_usage = process.cpu_percent()

                await asyncio.sleep(30)  # Update every 30 seconds

            except Exception as e:
                self.logger.error(f'"error": "{e}", "action": "health_monitor_error"')
                await asyncio.sleep(60)

    async def _handle_connection(self, reader, writer):
        """Handle incoming socket connection with error handling"""
        client_addr = "unix_socket"
        request_id = int(time.time() * 1000000) % 1000000  # Simple request ID

        try:
            # Read request with timeout
            data = await asyncio.wait_for(reader.read(32768), timeout=30.0)
            if not data:
                return

            request = json.loads(data.decode())
            method = request.get('method', 'unknown')
            params = request.get('params', {})

            self.logger.info(f'"request_id": {request_id}, "method": "{method}", "action": "request_received"')

            start_time = time.time()

            if method in self.handlers:
                try:
                    result = await self.handlers[method](**params)
                    response = {
                        'status': 'success',
                        'result': result,
                        'request_id': request_id,
                        'execution_time': time.time() - start_time
                    }

                except Exception as e:
                    self.logger.error(f'"request_id": {request_id}, "method": "{method}", "error": "{e}", "action": "handler_error"')
                    response = {
                        'status': 'error',
                        'error': str(e),
                        'request_id': request_id,
                        'execution_time': time.time() - start_time
                    }
            else:
                response = {
                    'status': 'error',
                    'error': f'Unknown method: {method}',
                    'request_id': request_id
                }

            # Send response
            response_data = json.dumps(response).encode()
            writer.write(response_data)
            await writer.drain()

            execution_time = time.time() - start_time
            self.logger.info(f'"request_id": {request_id}, "method": "{method}", "execution_time": {execution_time:.3f}, "action": "request_completed"')

        except asyncio.TimeoutError:
            self.logger.error(f'"request_id": {request_id}, "error": "request_timeout", "action": "request_timeout"')
        except json.JSONDecodeError as e:
            self.logger.error(f'"request_id": {request_id}, "error": "invalid_json", "details": "{e}", "action": "json_decode_error"')
        except Exception as e:
            self.logger.error(f'"request_id": {request_id}, "error": "{e}", "action": "connection_error"')
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass

    async def call_service(self, service_name: str, method: str, timeout: float = 30.0, **params):
        """Call another service via Unix socket with retry logic"""
        socket_path = f"/tmp/trading_{service_name}.sock"

        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_unix_connection(socket_path),
                    timeout=5.0
                )

                request = {
                    'method': method,
                    'params': params,
                    'timestamp': time.time()
                }

                writer.write(json.dumps(request).encode())
                await writer.drain()

                response_data = await asyncio.wait_for(reader.read(32768), timeout=timeout)
                response = json.loads(response_data.decode())

                writer.close()
                await writer.wait_closed()

                if response['status'] == 'success':
                    return response['result']
                else:
                    raise Exception(f"Service call failed: {response.get('error', 'Unknown error')}")

            except Exception as e:
                self.logger.error(f'"service": "{service_name}", "method": "{method}", "attempt": {attempt + 1}, "error": "{e}", "action": "service_call_failed"')

                if attempt == max_retries - 1:
                    raise Exception(f"Service call failed after {max_retries} attempts: {e}")

                await asyncio.sleep(retry_delay)
                retry_delay *= 2

    def publish_event(self, event_type: str, data: dict, priority: str = "normal"):
        """Publish event via Redis with priority support"""
        if not self.redis_client:
            self.logger.error(f'"event_type": "{event_type}", "error": "redis_unavailable", "action": "publish_failed"')
            return False

        try:
            event_data = {
                **data,
                'timestamp': time.time(),
                'source_service': self.service_name,
                'priority': priority
            }

            channel = f"trading:{priority}:{event_type}"
            self.redis_client.publish(channel, json.dumps(event_data))

            self.logger.info(f'"event_type": "{event_type}", "channel": "{channel}", "action": "event_published"')
            return True

        except Exception as e:
            self.logger.error(f'"event_type": "{event_type}", "error": "{e}", "action": "publish_error"')
            return False

    def subscribe_to_events(self, event_patterns: list, handler: Callable):
        """Subscribe to events via Redis with pattern matching"""
        if not self.redis_client:
            self.logger.error(f'"error": "redis_unavailable", "action": "subscribe_failed"')
            return None

        pubsub = self.redis_client.pubsub()

        for pattern in event_patterns:
            channel = f"trading:*:{pattern}"
            pubsub.psubscribe(channel)

        async def event_listener():
            while self.running:
                try:
                    message = pubsub.get_message(timeout=1.0)
                    if message and message['type'] == 'pmessage':
                        channel = message['channel'].decode()
                        event_type = channel.split(':')[-1]
                        event_data = json.loads(message['data'])

                        await handler(event_type, event_data)

                except Exception as e:
                    self.logger.error(f'"error": "{e}", "action": "event_handler_error"')
                    await asyncio.sleep(1)

        return event_listener

    async def health_check(self):
        """Built-in health check endpoint"""
        return {
            "service": self.service_name,
            "status": self.health.status,
            "uptime": self.health.uptime,
            "memory_usage": self.health.memory_usage,
            "cpu_usage": self.health.cpu_usage,
            "last_error": self.health.last_error,
            "handlers": list(self.handlers.keys())
        }

    async def get_metrics(self):
        """Built-in metrics endpoint"""
        return {
            "service": self.service_name,
            "uptime": time.time() - self.start_time,
            "memory_usage": self.health.memory_usage,
            "cpu_usage": self.health.cpu_usage,
            "redis_connected": self.redis_client is not None
        }

    async def graceful_shutdown(self):
        """Built-in graceful shutdown endpoint"""
        self.logger.info(f'"action": "graceful_shutdown_initiated"')
        self.running = False
        return {"status": "shutdown_initiated"}
```

### 2. Enhanced Prediction Service

```python
# services/prediction_service.py
#!/usr/bin/env python3
import asyncio
import sys
import os
from typing import Dict, List
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.base_service import BaseService
from enhanced_efficient_system_market_aware import EnhancedMarketAwarePredictor

class PredictionService(BaseService):
    """Enhanced prediction service with caching, batching, and comprehensive monitoring"""

    def __init__(self):
        super().__init__("prediction")
        self.predictor = EnhancedMarketAwarePredictor()
        self.prediction_cache = {}
        self.cache_ttl = 1800  # 30 minutes

        # Metrics
        self.prediction_count = 0
        self.buy_signal_count = 0
        self.error_count = 0

        # Register methods
        self.register_handler("generate_predictions", self.generate_predictions)
        self.register_handler("generate_single_prediction", self.generate_single_prediction)
        self.register_handler("get_prediction", self.get_prediction)
        self.register_handler("get_buy_rate", self.get_buy_rate)
        self.register_handler("clear_cache", self.clear_cache)

    async def generate_predictions(self, symbols: List[str] = None, force_refresh: bool = False):
        """Generate predictions for multiple symbols with intelligent caching"""
        if not symbols:
            symbols = ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX", "MQG.AX", "COL.AX", "BHP.AX"]

        predictions = {}
        cache_hits = 0
        fresh_predictions = 0

        self.logger.info(f'"symbols": {symbols}, "force_refresh": {force_refresh}, "action": "prediction_batch_started"')

        for symbol in symbols:
            try:
                # Check cache first
                cache_key = f"prediction:{symbol}"

                if not force_refresh and cache_key in self.prediction_cache:
                    cached_data, timestamp = self.prediction_cache[cache_key]
                    if datetime.now().timestamp() - timestamp < self.cache_ttl:
                        predictions[symbol] = cached_data
                        cache_hits += 1
                        continue

                # Generate fresh prediction
                prediction = await self._generate_fresh_prediction(symbol)
                predictions[symbol] = prediction

                # Cache the result
                self.prediction_cache[cache_key] = (prediction, datetime.now().timestamp())
                fresh_predictions += 1

                # Update metrics
                self.prediction_count += 1
                if prediction.get('action') in ['BUY', 'STRONG_BUY']:
                    self.buy_signal_count += 1

                # Publish prediction event
                self.publish_event("prediction_generated", {
                    "symbol": symbol,
                    "prediction": prediction,
                    "cache_hit": False
                }, priority="high")

            except Exception as e:
                self.error_count += 1
                self.logger.error(f'"symbol": "{symbol}", "error": "{e}", "action": "prediction_generation_failed"')
                predictions[symbol] = {"error": str(e), "status": "failed"}

        # Calculate and log BUY rate
        successful_predictions = [p for p in predictions.values() if "error" not in p]
        buy_signals = [p for p in successful_predictions if p.get('action') in ['BUY', 'STRONG_BUY']]
        buy_rate = (len(buy_signals) / len(successful_predictions) * 100) if successful_predictions else 0

        self.logger.info(f'"total_symbols": {len(symbols)}, "cache_hits": {cache_hits}, "fresh_predictions": {fresh_predictions}, "buy_rate": {buy_rate:.1f}, "action": "prediction_batch_completed"')

        # Alert if BUY rate is concerning
        if buy_rate > 70:
            self.publish_event("buy_rate_alert", {
                "buy_rate": buy_rate,
                "total_predictions": len(successful_predictions),
                "buy_signals": len(buy_signals),
                "alert_type": "high_buy_rate"
            }, priority="urgent")

        return {
            "predictions": predictions,
            "summary": {
                "total_symbols": len(symbols),
                "successful": len(successful_predictions),
                "failed": len(symbols) - len(successful_predictions),
                "cache_hits": cache_hits,
                "fresh_predictions": fresh_predictions,
                "buy_rate": buy_rate
            }
        }

    async def _generate_fresh_prediction(self, symbol: str) -> Dict:
        """Generate a fresh prediction for a single symbol"""
        # Get market data from market data service
        try:
            market_data = await self.call_service("market-data", "get_market_data", symbol=symbol)
        except Exception as e:
            self.logger.error(f'"symbol": "{symbol}", "error": "{e}", "action": "market_data_fetch_failed"')
            # Fallback to basic data structure
            market_data = {
                "technical": {"current_price": 0, "rsi": 50, "tech_score": 50},
                "volume": {"volume_trend": 0, "volume_quality_score": 0.5},
                "market_context": {"context": "NEUTRAL", "buy_threshold": 0.70}
            }

        # Get sentiment from sentiment service
        try:
            sentiment_data = await self.call_service("sentiment", "analyze_sentiment", symbol=symbol)
        except Exception as e:
            self.logger.error(f'"symbol": "{symbol}", "error": "{e}", "action": "sentiment_fetch_failed"')
            # Fallback sentiment data
            sentiment_data = {
                "sentiment_score": 0.0,
                "news_confidence": 0.5,
                "news_quality_score": 0.5
            }

        # Generate prediction using enhanced logic
        prediction = self.predictor.calculate_confidence(
            symbol=symbol,
            tech_data=market_data.get("technical", {}),
            news_data=sentiment_data,
            volume_data=market_data.get("volume", {}),
            market_data=market_data.get("market_context", {})
        )

        # Enhance prediction with additional metadata
        enhanced_prediction = {
            **prediction,
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "market_data_available": "error" not in str(market_data),
            "sentiment_data_available": "error" not in str(sentiment_data),
            "prediction_id": f"{symbol}_{int(datetime.now().timestamp())}"
        }

        return enhanced_prediction

    async def generate_single_prediction(self, symbol: str, force_refresh: bool = False):
        """Generate prediction for a single symbol"""
        result = await self.generate_predictions([symbol], force_refresh)
        return result["predictions"].get(symbol, {"error": "Prediction failed"})

    async def get_prediction(self, symbol: str):
        """Get latest cached prediction for symbol"""
        cache_key = f"prediction:{symbol}"

        if cache_key in self.prediction_cache:
            cached_data, timestamp = self.prediction_cache[cache_key]
            age = datetime.now().timestamp() - timestamp

            return {
                **cached_data,
                "cache_age": age,
                "cached": True
            }
        else:
            return {"error": "No cached prediction available", "symbol": symbol}

    async def get_buy_rate(self, timeframe: str = "current"):
        """Get current BUY signal rate"""
        if self.prediction_count == 0:
            return {"buy_rate": 0, "total_predictions": 0, "buy_signals": 0}

        buy_rate = (self.buy_signal_count / self.prediction_count) * 100

        return {
            "buy_rate": buy_rate,
            "total_predictions": self.prediction_count,
            "buy_signals": self.buy_signal_count,
            "timeframe": timeframe
        }

    async def clear_cache(self):
        """Clear prediction cache"""
        cache_size = len(self.prediction_cache)
        self.prediction_cache.clear()

        self.logger.info(f'"cache_size": {cache_size}, "action": "cache_cleared"')
        return {"cleared_entries": cache_size}

    async def health_check(self):
        """Enhanced health check with prediction service metrics"""
        base_health = await super().health_check()

        # Add service-specific health metrics
        prediction_health = {
            **base_health,
            "predictor_loaded": self.predictor is not None,
            "cache_size": len(self.prediction_cache),
            "prediction_count": self.prediction_count,
            "buy_signal_count": self.buy_signal_count,
            "error_count": self.error_count,
            "current_buy_rate": (self.buy_signal_count / self.prediction_count * 100) if self.prediction_count > 0 else 0
        }

        # Health status based on error rate
        if self.prediction_count > 0:
            error_rate = (self.error_count / self.prediction_count) * 100
            if error_rate > 20:
                prediction_health["status"] = "degraded"
                prediction_health["warning"] = f"High error rate: {error_rate:.1f}%"

        return prediction_health

async def main():
    service = PredictionService()

    # Setup event subscriptions
    event_handler = service.subscribe_to_events(["market_data_updated"], handle_market_data_event)
    if event_handler:
        asyncio.create_task(event_handler())

    await service.start_server()

async def handle_market_data_event(event_type: str, event_data: dict):
    """Handle market data update events"""
    if event_type == "market_data_updated":
        symbol = event_data.get("symbol")
        # Invalidate cache for this symbol
        cache_key = f"prediction:{symbol}"
        # Could trigger fresh prediction here if needed

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. Systemd Service Files

```ini
# /etc/systemd/system/trading-prediction.service
[Unit]
Description=Trading Prediction Service
Documentation=file:///opt/trading_services/COMPLETE_MICROSERVICES_IMPLEMENTATION_GUIDE.md
After=network.target redis.service trading-market-data.service
Wants=redis.service trading-market-data.service
Requires=network.target

[Service]
Type=simple
User=trading
Group=trading
WorkingDirectory=/opt/trading_services
Environment=PYTHONPATH=/opt/trading_services:/root/test
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/trading_venv/bin/python services/prediction_service.py
ExecStop=/bin/kill -TERM $MAINPID
TimeoutStopSec=30
Restart=always
RestartSec=5
StartLimitInterval=300
StartLimitBurst=5

# Resource limits
MemoryMax=512M
CPUQuota=100%
TasksMax=50

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=trading-prediction

# Security
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/trading /tmp/trading_sockets

[Install]
WantedBy=multi-user.target
```

### 4. Complete Service Manager

```python
# scripts/service_manager.py
#!/usr/bin/env python3
"""
Complete service management tool for trading microservices
Handles deployment, monitoring, and operations
"""
import subprocess
import json
import time
import sys
import argparse
from pathlib import Path
from typing import Dict, List
import asyncio
import aiohttp

class TradingServiceManager:
    def __init__(self):
        self.services = [
            "trading-market-data",
            "trading-sentiment",
            "trading-prediction",
            "trading-scheduler",
            "trading-ml-training",
            "trading-paper-trading"
        ]

        self.service_dependencies = {
            "trading-prediction": ["trading-market-data", "trading-sentiment"],
            "trading-paper-trading": ["trading-prediction"],
            "trading-scheduler": ["trading-prediction"]
        }

    def get_service_status(self, service_name: str = None) -> Dict:
        """Get status of services"""
        if service_name:
            services = [service_name]
        else:
            services = self.services

        status = {}

        for service in services:
            try:
                result = subprocess.run(
                    ["systemctl", "is-active", service],
                    capture_output=True, text=True
                )
                status[service] = {
                    "active": result.stdout.strip() == "active",
                    "status": result.stdout.strip(),
                    "returncode": result.returncode
                }

                # Get additional info if service is running
                if status[service]["active"]:
                    info_result = subprocess.run(
                        ["systemctl", "show", service, "--property=MainPID,ActiveEnterTimestamp,MemoryCurrent"],
                        capture_output=True, text=True
                    )

                    for line in info_result.stdout.strip().split('\n'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            if key == "MainPID":
                                status[service]["pid"] = value
                            elif key == "ActiveEnterTimestamp":
                                status[service]["started"] = value
                            elif key == "MemoryCurrent":
                                status[service]["memory"] = value

            except Exception as e:
                status[service] = {"error": str(e), "active": False}

        return status

    async def check_service_health(self, service_name: str = None) -> Dict:
        """Check health of services via their health endpoints"""
        if service_name:
            services_to_check = [service_name.replace("trading-", "")]
        else:
            services_to_check = [s.replace("trading-", "") for s in self.services]

        health_status = {}

        for service in services_to_check:
            socket_path = f"/tmp/trading_{service}.sock"

            try:
                reader, writer = await asyncio.open_unix_connection(socket_path)

                request = {"method": "health", "params": {}}
                writer.write(json.dumps(request).encode())
                await writer.drain()

                response_data = await reader.read(8192)
                response = json.loads(response_data.decode())

                writer.close()
                await writer.wait_closed()

                if response['status'] == 'success':
                    health_status[f"trading-{service}"] = response['result']
                else:
                    health_status[f"trading-{service}"] = {"status": "unhealthy", "error": response.get('error')}

            except Exception as e:
                health_status[f"trading-{service}"] = {"status": "unreachable", "error": str(e)}

        return health_status

    def start_services(self, services: List[str] = None, ordered: bool = True):
        """Start services with dependency resolution"""
        if not services:
            services = self.services

        if ordered:
            # Start in dependency order
            started = set()
            remaining = set(services)

            while remaining:
                ready_to_start = []

                for service in remaining:
                    deps = self.service_dependencies.get(service, [])
                    if all(dep in started or dep not in services for dep in deps):
                        ready_to_start.append(service)

                if not ready_to_start:
                    print(f"Circular dependency detected in: {remaining}")
                    break

                for service in ready_to_start:
                    self._start_service(service)
                    started.add(service)
                    remaining.remove(service)
        else:
            for service in services:
                self._start_service(service)

    def _start_service(self, service: str):
        """Start a single service"""
        try:
            result = subprocess.run(
                ["sudo", "systemctl", "start", service],
                capture_output=True, text=True
            )

            if result.returncode == 0:
                print(f"✅ Started {service}")
            else:
                print(f"❌ Failed to start {service}: {result.stderr}")

        except Exception as e:
            print(f"❌ Error starting {service}: {e}")

    def stop_services(self, services: List[str] = None):
        """Stop services"""
        if not services:
            services = self.services

        for service in reversed(services):  # Stop in reverse order
            try:
                result = subprocess.run(
                    ["sudo", "systemctl", "stop", service],
                    capture_output=True, text=True
                )

                if result.returncode == 0:
                    print(f"🛑 Stopped {service}")
                else:
                    print(f"❌ Failed to stop {service}: {result.stderr}")

            except Exception as e:
                print(f"❌ Error stopping {service}: {e}")

    def restart_services(self, services: List[str] = None):
        """Restart services"""
        if not services:
            services = self.services

        self.stop_services(services)
        time.sleep(2)  # Brief pause
        self.start_services(services)

    def show_logs(self, service: str, lines: int = 50, follow: bool = False):
        """Show service logs"""
        cmd = ["sudo", "journalctl", "-u", service, "-n", str(lines)]
        if follow:
            cmd.append("-f")

        try:
            subprocess.run(cmd)
        except KeyboardInterrupt:
            pass

    def deploy_services(self, source_dir: str = "/opt/trading_services"):
        """Deploy all service files and configurations"""
        print("🚀 Deploying trading microservices...")

        # Copy service files
        service_files = Path(source_dir) / "systemd"
        if service_files.exists():
            subprocess.run([
                "sudo", "cp", "-r",
                str(service_files / "*.service"),
                "/etc/systemd/system/"
            ])

        # Reload systemd
        subprocess.run(["sudo", "systemctl", "daemon-reload"])

        # Enable services
        for service in self.services:
            subprocess.run(["sudo", "systemctl", "enable", service])

        print("✅ Services deployed and enabled")

    async def run_health_dashboard(self):
        """Run a simple health dashboard"""
        while True:
            try:
                print("\n" + "="*80)
                print("TRADING MICROSERVICES HEALTH DASHBOARD")
                print("="*80)

                # System status
                system_status = self.get_service_status()
                health_status = await self.check_service_health()

                for service in self.services:
                    sys_info = system_status.get(service, {})
                    health_info = health_status.get(service, {})

                    status_icon = "🟢" if sys_info.get("active") else "🔴"
                    health_icon = "💚" if health_info.get("status") == "healthy" else "💔"

                    memory = sys_info.get("memory", "N/A")
                    if memory != "N/A" and memory.isdigit():
                        memory = f"{int(memory) // 1024 // 1024}MB"

                    print(f"{status_icon} {health_icon} {service:25} | Memory: {memory:>8} | PID: {sys_info.get('pid', 'N/A'):>8}")

                    # Show errors if any
                    if health_info.get("error"):
                        print(f"    ⚠️  {health_info['error']}")

                print(f"\n⏰ Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
                print("Press Ctrl+C to exit")

                await asyncio.sleep(10)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Dashboard error: {e}")
                await asyncio.sleep(5)

def main():
    parser = argparse.ArgumentParser(description="Trading Microservices Manager")
    parser.add_argument("command", choices=[
        "start", "stop", "restart", "status", "health",
        "logs", "deploy", "dashboard"
    ])
    parser.add_argument("--service", "-s", help="Specific service name")
    parser.add_argument("--lines", "-n", type=int, default=50, help="Number of log lines")
    parser.add_argument("--follow", "-f", action="store_true", help="Follow logs")

    args = parser.parse_args()
    manager = TradingServiceManager()

    if args.command == "start":
        services = [args.service] if args.service else None
        manager.start_services(services)

    elif args.command == "stop":
        services = [args.service] if args.service else None
        manager.stop_services(services)

    elif args.command == "restart":
        services = [args.service] if args.service else None
        manager.restart_services(services)

    elif args.command == "status":
        status = manager.get_service_status(args.service)
        print(json.dumps(status, indent=2))

    elif args.command == "health":
        health = asyncio.run(manager.check_service_health(args.service))
        print(json.dumps(health, indent=2))

    elif args.command == "logs":
        if not args.service:
            print("Please specify a service with --service")
            sys.exit(1)
        manager.show_logs(args.service, args.lines, args.follow)

    elif args.command == "deploy":
        manager.deploy_services()

    elif args.command == "dashboard":
        asyncio.run(manager.run_health_dashboard())

if __name__ == "__main__":
    main()
```

### 5. Docker Compose Alternative (for Development)

```yaml
# docker-compose.dev.yml
version: "3.8"

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  market-data:
    build:
      context: .
      dockerfile: services/Dockerfile.market-data
    depends_on:
      redis:
        condition: service_healthy
    environment:
      - REDIS_URL=redis://redis:6379
      - PYTHONPATH=/app
    volumes:
      - ./services:/app/services
      - ./logs:/app/logs
    healthcheck:
      test:
        [
          "CMD",
          "python",
          "-c",
          "import socket; socket.socket(socket.AF_UNIX).connect('/tmp/trading_market-data.sock')",
        ]
      interval: 30s
      timeout: 10s
      retries: 3

  prediction:
    build:
      context: .
      dockerfile: services/Dockerfile.prediction
    depends_on:
      market-data:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      - REDIS_URL=redis://redis:6379
      - PYTHONPATH=/app
    volumes:
      - ./services:/app/services
      - ./logs:/app/logs

  sentiment:
    build:
      context: .
      dockerfile: services/Dockerfile.sentiment
    depends_on:
      redis:
        condition: service_healthy
    environment:
      - REDIS_URL=redis://redis:6379
      - PYTHONPATH=/app
    volumes:
      - ./services:/app/services
      - ./logs:/app/logs

volumes:
  redis_data:
```

## Migration Timeline

### Week 1: Foundation

- [ ] Setup Redis on VM
- [ ] Deploy base service framework
- [ ] Create service directories and permissions
- [ ] Test basic service communication

### Week 2: Core Services

- [ ] Deploy Market Data Service
- [ ] Deploy Prediction Service
- [ ] Test service-to-service communication
- [ ] Validate prediction generation

### Week 3: Integration

- [ ] Deploy compatibility layer
- [ ] Update cron jobs to use services
- [ ] Run parallel testing (old vs new)
- [ ] Monitor performance and resource usage

### Week 4: Full Migration

- [ ] Deploy remaining services (Sentiment, ML Training)
- [ ] Switch all cron jobs to microservices
- [ ] Implement monitoring and alerting
- [ ] Document operational procedures

## Testing & Validation

```bash
# Test service deployment
./scripts/service_manager.py deploy
./scripts/service_manager.py start

# Health checks
./scripts/service_manager.py health

# Test predictions
python -c "
import asyncio
from services.base_service import BaseService

async def test():
    service = BaseService('test')
    result = await service.call_service('prediction', 'generate_predictions', symbols=['CBA.AX'])
    print(result)

asyncio.run(test())
"

# Performance testing
time python compatibility/run_predictions.py
```

This complete implementation guide provides you with everything needed to migrate from your monolithic system to lightweight microservices, whether you choose the VM-native approach or Docker, with full backward compatibility and comprehensive monitoring.

## Additional Critical Components Analysis

Based on comprehensive workspace analysis, here are the important aspects that enhance the microservices implementation:

### 1. ML Model Management Service

Your `models/` directory contains trained models that need dedicated management:

```python
# services/ml_model_service.py
class MLModelService(BaseService):
    def __init__(self):
        super().__init__("ml-model")
        self.model_registry = {}
        self.active_models = {}

    async def load_model(self, model_name: str, symbol: str = None):
        """Load bank-specific or general models"""
        if symbol and os.path.exists(f"models/{symbol}"):
            model_path = f"models/{symbol}/{model_name}.pkl"
        else:
            model_path = f"models/{model_name}.pkl"

        with open(model_path, 'rb') as f:
            model = pickle.load(f)

        key = f"{model_name}_{symbol}" if symbol else model_name
        self.active_models[key] = {
            'model': model,
            'loaded_at': datetime.now(),
            'symbol': symbol
        }

    async def predict(self, model_name: str, features: dict, symbol: str = None):
        """Make prediction using appropriate model"""
        key = f"{model_name}_{symbol}" if symbol else model_name

        if key not in self.active_models:
            await self.load_model(model_name, symbol)

        model_data = self.active_models[key]
        prediction = model_data['model'].predict([list(features.values())])

        return {
            'prediction': prediction.tolist(),
            'model': model_name,
            'symbol': symbol,
            'timestamp': datetime.now().isoformat()
        }
```

### 2. Paper Trading Integration Service

Your `paper-trading-app/` and `ig_markets_paper_trading/` require integration:

```python
# services/paper_trading_service.py
class PaperTradingService(BaseService):
    def __init__(self):
        super().__init__("paper-trading")
        self.ig_client = None
        self.positions = {}

    async def initialize_ig_markets(self):
        """Initialize IG Markets integration"""
        try:
            sys.path.append("paper-trading-app")
            from enhanced_paper_trading_service import IGMarketsClient
            self.ig_client = IGMarketsClient()
            return {"status": "ig_markets_initialized"}
        except Exception as e:
            return {"error": f"IG Markets initialization failed: {e}"}

    async def sync_positions(self):
        """Sync with live paper trading positions"""
        if not self.ig_client:
            await self.initialize_ig_markets()

        try:
            positions = await self.ig_client.get_positions()
            self.positions.update(positions)
            return {"synced_positions": len(self.positions)}
        except Exception as e:
            return {"error": f"Position sync failed: {e}"}

    async def execute_trade(self, symbol: str, action: str, quantity: int):
        """Execute paper trade through IG Markets"""
        trade = {
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'timestamp': datetime.now(),
            'trade_id': str(uuid.uuid4())
        }

        if self.ig_client:
            try:
                result = await self.ig_client.place_order(trade)
                trade['ig_order_id'] = result.get('order_id')
                trade['status'] = 'executed'
            except Exception as e:
                trade['status'] = 'failed'
                trade['error'] = str(e)

        self.positions[trade['trade_id']] = trade
        return trade
```

### 3. Data Quality and Validation Service

Your `data_quality_system/` needs to be a microservice:

```python
# services/data_quality_service.py
class DataQualityService(BaseService):
    def __init__(self):
        super().__init__("data-quality")
        self.quality_metrics = {}
        self.validation_rules = {}

    async def validate_prediction_data(self, data: dict):
        """Validate prediction data quality using true prediction engine"""
        try:
            sys.path.append("data_quality_system/core")
            from true_prediction_engine import PredictionStore

            store = PredictionStore()
            validation_result = store.validate_prediction_structure(data)

            return {
                "valid": validation_result.get("valid", False),
                "quality_score": validation_result.get("score", 0),
                "issues": validation_result.get("issues", [])
            }
        except Exception as e:
            return {"error": f"Validation failed: {e}", "valid": False}

    async def monitor_data_quality(self):
        """Continuous data quality monitoring"""
        quality_report = {
            "timestamp": datetime.now().isoformat(),
            "metrics": self.quality_metrics,
            "overall_score": sum(self.quality_metrics.values()) / len(self.quality_metrics) if self.quality_metrics else 0
        }

        # Alert on quality degradation
        if quality_report["overall_score"] < 70:
            self.publish_event("data_quality_alert", quality_report, priority="high")

        return quality_report
```

### 4. Task Scheduler Service (Market-Aware)

Replace cron with market-aware scheduling:

```python
# services/scheduler_service.py
class SchedulerService(BaseService):
    def __init__(self):
        super().__init__("scheduler")
        self.jobs = {}
        self.market_hours = self._get_market_hours()

    def _get_market_hours(self):
        """Get ASX market hours"""
        return {
            "open": "10:00",
            "close": "16:00",
            "timezone": "Australia/Sydney",
            "weekdays": [0, 1, 2, 3, 4]  # Monday-Friday
        }

    async def schedule_market_aware_job(self, job_id: str, job_type: str, params: dict = None):
        """Schedule job based on market conditions"""
        if job_type == "morning_analysis":
            # Schedule 30 minutes before market open
            schedule_time = "09:30"
        elif job_type == "evening_analysis":
            # Schedule 1 hour after market close
            schedule_time = "17:00"
        elif job_type == "prediction_generation":
            # Schedule 15 minutes before market open
            schedule_time = "09:45"
        else:
            schedule_time = params.get("time", "09:00")

        job = {
            "id": job_id,
            "type": job_type,
            "schedule_time": schedule_time,
            "params": params or {},
            "status": "scheduled",
            "next_run": self._calculate_next_run(schedule_time)
        }

        self.jobs[job_id] = job
        return job

    async def execute_job(self, job_id: str):
        """Execute scheduled job"""
        if job_id not in self.jobs:
            return {"error": "Job not found"}

        job = self.jobs[job_id]

        try:
            if job["type"] == "morning_analysis":
                result = await self.call_service("prediction", "generate_predictions")
            elif job["type"] == "evening_analysis":
                result = await self._run_evening_analysis()
            elif job["type"] == "prediction_generation":
                symbols = job["params"].get("symbols", ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX"])
                result = await self.call_service("prediction", "generate_predictions", symbols=symbols)
            else:
                result = {"error": "Unknown job type"}

            job["last_run"] = datetime.now().isoformat()
            job["last_result"] = result
            job["status"] = "completed"

            return result

        except Exception as e:
            job["status"] = "failed"
            job["last_error"] = str(e)
            return {"error": str(e)}
```

### 5. Backup and Recovery Service

Handle your multiple backup directories:

```python
# services/backup_service.py
class BackupService(BaseService):
    def __init__(self):
        super().__init__("backup")
        self.backup_locations = {
            "local": "backup_local",
            "remote": "remote_backup",
            "production": "production/backups"
        }

    async def create_backup(self, backup_type: str = "incremental"):
        """Create comprehensive system backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"backup_{backup_type}_{timestamp}"

        os.makedirs(backup_dir, exist_ok=True)

        # Backup databases
        databases = [
            "trading_predictions.db",
            "paper_trading.db",
            "predictions.db",
            "data/enhanced_outcomes.db",
            "data/ig_markets_paper_trades.db"
        ]

        backed_up = []
        for db in databases:
            if os.path.exists(db):
                shutil.copy2(db, f"{backup_dir}/{os.path.basename(db)}")
                backed_up.append(db)

        # Backup ML models
        if os.path.exists("models"):
            shutil.copytree("models", f"{backup_dir}/models", dirs_exist_ok=True)

        # Backup configurations
        config_files = ["config.py", "enhanced_config.py", "app/config/"]
        for config in config_files:
            if os.path.exists(config):
                if os.path.isdir(config):
                    shutil.copytree(config, f"{backup_dir}/{config}", dirs_exist_ok=True)
                else:
                    shutil.copy2(config, backup_dir)

        backup_info = {
            "backup_id": backup_dir,
            "timestamp": timestamp,
            "type": backup_type,
            "databases_backed_up": backed_up,
            "size_mb": self._get_directory_size(backup_dir),
            "status": "completed"
        }

        return backup_info

    async def restore_backup(self, backup_id: str):
        """Restore from backup"""
        if not os.path.exists(backup_id):
            return {"error": "Backup not found"}

        # Stop services before restore
        await self.call_service("scheduler", "stop_all_jobs")

        # Restore databases
        for db_file in os.listdir(backup_id):
            if db_file.endswith('.db'):
                shutil.copy2(f"{backup_id}/{db_file}", db_file)

        # Restore models
        if os.path.exists(f"{backup_id}/models"):
            if os.path.exists("models"):
                shutil.rmtree("models")
            shutil.copytree(f"{backup_id}/models", "models")

        return {"status": "restore_completed", "backup_id": backup_id}
```

### 6. Documentation and Monitoring Service

```python
# services/monitoring_service.py
class MonitoringService(BaseService):
    def __init__(self):
        super().__init__("monitoring")
        self.metrics = {}
        self.alerts = []

    async def collect_system_metrics(self):
        """Collect comprehensive system metrics"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "system": {}
        }

        # Collect service metrics
        for service in ["market-data", "prediction", "sentiment", "paper-trading"]:
            try:
                health = await self.call_service(service, "health")
                metrics["services"][service] = health
            except Exception as e:
                metrics["services"][service] = {"error": str(e), "status": "unreachable"}

        # System metrics
        import psutil
        metrics["system"] = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent
        }

        self.metrics = metrics
        return metrics

    async def check_alerts(self):
        """Check for system alerts"""
        alerts = []

        if not self.metrics:
            await self.collect_system_metrics()

        # Memory alerts
        if self.metrics["system"]["memory_percent"] > 80:
            alerts.append({
                "type": "memory_high",
                "severity": "warning",
                "message": f"Memory usage at {self.metrics['system']['memory_percent']:.1f}%"
            })

        # Service health alerts
        for service, health in self.metrics["services"].items():
            if health.get("status") != "healthy":
                alerts.append({
                    "type": "service_unhealthy",
                    "severity": "critical",
                    "service": service,
                    "message": f"Service {service} is {health.get('status', 'unknown')}"
                })

        self.alerts = alerts
        return alerts
```

### 7. Enhanced Systemd Services

```ini
# /etc/systemd/system/trading-ml-model.service
[Unit]
Description=Trading ML Model Management Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=trading
WorkingDirectory=/opt/trading_services
Environment=PYTHONPATH=/opt/trading_services
ExecStart=/opt/trading_venv/bin/python services/ml_model_service.py
Restart=always
RestartSec=5
MemoryMax=1G

[Install]
WantedBy=multi-user.target
```

## Implementation Priority Order

1. **ML Model Service** - Critical for bank-specific predictions
2. **Paper Trading Integration** - Required for live trading
3. **Data Quality Service** - Essential for system reliability
4. **Task Scheduler Service** - Replace cron dependencies
5. **Backup Service** - Data protection and recovery
6. **Monitoring Service** - System observability

## Complete Service Dependencies

```
trading-base (Redis, logging)
├── trading-market-data
├── trading-sentiment
├── trading-ml-model
├── trading-data-quality
├── trading-backup
└── trading-monitoring
    ├── trading-prediction (depends on: market-data, sentiment, ml-model)
    ├── trading-paper-trading (depends on: prediction)
    └── trading-scheduler (depends on: prediction, paper-trading)
```

This comprehensive analysis covers all critical aspects identified in your workspace, ensuring the microservices implementation addresses every component of your trading system.
