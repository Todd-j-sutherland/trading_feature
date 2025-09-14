"""
Base Service Framework for Trading Microservices

This is the foundational service class that all trading microservices inherit from.
It provides:
- Unix socket communication
- Redis pub/sub event system
- Structured logging with JSON format
- Health monitoring and metrics
- Graceful shutdown handling
- Service-to-service communication
- Error handling and retry logic

Based on the microservices implementation guides in:
- .github/instructions/microservices.instructions.md
- COMPLETE_MICROSERVICES_IMPLEMENTATION_GUIDE.md

Usage:
    class MyService(BaseService):
        def __init__(self):
            super().__init__("my-service")
            self.register_handler("my_method", self.handle_method)
        
        async def handle_method(self, param1, param2):
            return {"result": "success"}

Key Features:
- Automatic health checks at /tmp/trading_{service_name}.sock
- Redis integration for event publishing/subscribing
- Comprehensive error logging and metrics
- Memory and CPU monitoring
- Built-in graceful shutdown
"""

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
    """Base class for all trading microservices with health checks, metrics, and error handling"""

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
