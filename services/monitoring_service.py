#!/usr/bin/env python3
"""
Comprehensive Monitoring and Observability Service

This service provides enterprise-grade monitoring, metrics collection, alerting, and observability
for the trading microservices architecture.

Features:
- Real-time metrics collection and aggregation
- Automated alerting with multiple channels (email, webhook, console)
- Service health monitoring with dependency tracking
- Performance analytics and trend analysis
- Custom dashboard data export
- Log aggregation and analysis
- SLA monitoring and reporting

Author: Trading System Monitoring Framework
Date: September 14, 2025
"""

import asyncio
import json
import time
import logging
import smtplib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import threading
import queue
import sqlite3
import statistics
import psutil
import redis
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.base_service import BaseService

@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: float
    service: str
    metric_name: str
    value: float
    tags: Dict[str, str] = None
    
@dataclass
class ServiceHealth:
    """Comprehensive service health status"""
    service_name: str
    status: str
    uptime: float
    cpu_usage: float
    memory_usage: int
    response_time: float
    error_rate: float
    last_error: Optional[str] = None
    dependencies_healthy: bool = True
    sla_compliance: float = 100.0
    
@dataclass
class Alert:
    """Alert configuration and state"""
    alert_id: str
    alert_type: str
    severity: str  # critical, warning, info
    condition: str
    threshold: float
    current_value: float
    service: str
    message: str
    created_at: float
    resolved_at: Optional[float] = None
    notification_sent: bool = False

class MetricsCollector:
    """Advanced metrics collection and storage system"""
    
    def __init__(self, db_path: str = "data/metrics.db"):
        self.db_path = db_path
        self.metrics_queue = queue.Queue(maxsize=10000)
        self.batch_size = 100
        self.flush_interval = 30  # seconds
        
        # Initialize database
        self._init_database()
        
        # Start background processing
        self.running = True
        self.processor_thread = threading.Thread(target=self._process_metrics_loop, daemon=True)
        self.processor_thread.start()
        
    def _init_database(self):
        """Initialize metrics database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    service TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    tags TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_timestamp 
                ON metrics(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_service_metric 
                ON metrics(service, metric_name)
            """)
            
    def record_metric(self, metric: MetricPoint):
        """Record a metric point"""
        try:
            self.metrics_queue.put_nowait(metric)
        except queue.Full:
            # If queue is full, drop oldest metrics
            try:
                self.metrics_queue.get_nowait()
                self.metrics_queue.put_nowait(metric)
            except queue.Empty:
                pass
                
    def _process_metrics_loop(self):
        """Background thread to process and store metrics"""
        batch = []
        last_flush = time.time()
        
        while self.running:
            try:
                # Get metric with timeout
                try:
                    metric = self.metrics_queue.get(timeout=1.0)
                    batch.append(metric)
                except queue.Empty:
                    pass
                
                # Flush batch if full or time elapsed
                current_time = time.time()
                if (len(batch) >= self.batch_size or 
                    (batch and current_time - last_flush >= self.flush_interval)):
                    
                    self._flush_batch(batch)
                    batch = []
                    last_flush = current_time
                    
            except Exception as e:
                logging.error(f"Metrics processing error: {e}")
                time.sleep(1)
                
    def _flush_batch(self, batch: List[MetricPoint]):
        """Flush metrics batch to database"""
        if not batch:
            return
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.executemany("""
                    INSERT INTO metrics (timestamp, service, metric_name, value, tags)
                    VALUES (?, ?, ?, ?, ?)
                """, [
                    (m.timestamp, m.service, m.metric_name, m.value, 
                     json.dumps(m.tags) if m.tags else None)
                    for m in batch
                ])
                
        except Exception as e:
            logging.error(f"Failed to flush metrics batch: {e}")
            
    def get_metrics(self, service: str = None, metric_name: str = None, 
                   start_time: float = None, end_time: float = None, 
                   limit: int = 1000) -> List[Dict]:
        """Query metrics from database"""
        try:
            conditions = []
            params = []
            
            if service:
                conditions.append("service = ?")
                params.append(service)
                
            if metric_name:
                conditions.append("metric_name = ?")
                params.append(metric_name)
                
            if start_time:
                conditions.append("timestamp >= ?")
                params.append(start_time)
                
            if end_time:
                conditions.append("timestamp <= ?")
                params.append(end_time)
                
            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
            
            query = f"""
                SELECT timestamp, service, metric_name, value, tags
                FROM metrics
                {where_clause}
                ORDER BY timestamp DESC
                LIMIT ?
            """
            params.append(limit)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(query, params)
                return [
                    {
                        'timestamp': row[0],
                        'service': row[1],
                        'metric_name': row[2],
                        'value': row[3],
                        'tags': json.loads(row[4]) if row[4] else {}
                    }
                    for row in cursor.fetchall()
                ]
                
        except Exception as e:
            logging.error(f"Failed to query metrics: {e}")
            return []

class AlertManager:
    """Advanced alerting system with multiple notification channels"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.notification_channels = []
        self.cooldown_period = 300  # 5 minutes between duplicate alerts
        
        # Setup notification channels
        self._setup_notification_channels()
        
    def _setup_notification_channels(self):
        """Setup available notification channels"""
        # Console notifications (always available)
        self.notification_channels.append(self._console_notify)
        
        # Email notifications (if configured)
        if self.config.get('email', {}).get('enabled', False):
            self.notification_channels.append(self._email_notify)
            
        # Webhook notifications (if configured)
        if self.config.get('webhook', {}).get('enabled', False):
            self.notification_channels.append(self._webhook_notify)
            
    def create_alert(self, alert_type: str, service: str, severity: str,
                    condition: str, threshold: float, current_value: float,
                    message: str) -> str:
        """Create new alert"""
        alert_id = f"{service}_{alert_type}_{int(time.time())}"
        
        alert = Alert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            condition=condition,
            threshold=threshold,
            current_value=current_value,
            service=service,
            message=message,
            created_at=time.time()
        )
        
        # Check for duplicate recent alerts
        recent_similar = [
            a for a in self.alert_history[-50:]  # Check last 50 alerts
            if (a.service == service and 
                a.alert_type == alert_type and
                a.created_at > time.time() - self.cooldown_period)
        ]
        
        if not recent_similar:
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)
            self._send_notifications(alert)
            
        return alert_id
        
    def resolve_alert(self, alert_id: str):
        """Resolve an active alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved_at = time.time()
            
            # Send resolution notification
            resolution_message = f"RESOLVED: {alert.message}"
            resolution_alert = Alert(
                alert_id=f"{alert_id}_resolved",
                alert_type=f"{alert.alert_type}_resolved",
                severity="info",
                condition="resolved",
                threshold=alert.threshold,
                current_value=alert.current_value,
                service=alert.service,
                message=resolution_message,
                created_at=time.time()
            )
            
            self._send_notifications(resolution_alert)
            del self.active_alerts[alert_id]
            
    def _send_notifications(self, alert: Alert):
        """Send alert through all configured channels"""
        for channel in self.notification_channels:
            try:
                channel(alert)
            except Exception as e:
                logging.error(f"Failed to send alert via {channel.__name__}: {e}")
                
    def _console_notify(self, alert: Alert):
        """Console notification"""
        severity_icons = {
            'critical': '🚨',
            'warning': '⚠️',
            'info': 'ℹ️'
        }
        
        icon = severity_icons.get(alert.severity, '📢')
        timestamp = datetime.fromtimestamp(alert.created_at).strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"\n{icon} ALERT [{alert.severity.upper()}] - {timestamp}")
        print(f"Service: {alert.service}")
        print(f"Type: {alert.alert_type}")
        print(f"Message: {alert.message}")
        print(f"Threshold: {alert.threshold}, Current: {alert.current_value}")
        print("-" * 60)
        
    def _email_notify(self, alert: Alert):
        """Email notification"""
        email_config = self.config.get('email', {})
        
        msg = MimeMultipart()
        msg['From'] = email_config.get('from_email')
        msg['To'] = ', '.join(email_config.get('to_emails', []))
        msg['Subject'] = f"Trading System Alert: {alert.service} - {alert.alert_type}"
        
        body = f"""
        Alert Details:
        - Service: {alert.service}
        - Alert Type: {alert.alert_type}
        - Severity: {alert.severity}
        - Message: {alert.message}
        - Threshold: {alert.threshold}
        - Current Value: {alert.current_value}
        - Time: {datetime.fromtimestamp(alert.created_at)}
        
        This is an automated alert from the Trading System Monitoring Service.
        """
        
        msg.attach(MimeText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(email_config.get('smtp_server'), email_config.get('smtp_port', 587))
        server.starttls()
        server.login(email_config.get('username'), email_config.get('password'))
        server.send_message(msg)
        server.quit()
        
    def _webhook_notify(self, alert: Alert):
        """Webhook notification"""
        webhook_config = self.config.get('webhook', {})
        
        payload = {
            'alert_id': alert.alert_id,
            'service': alert.service,
            'alert_type': alert.alert_type,
            'severity': alert.severity,
            'message': alert.message,
            'threshold': alert.threshold,
            'current_value': alert.current_value,
            'timestamp': alert.created_at
        }
        
        requests.post(
            webhook_config.get('url'),
            json=payload,
            headers=webhook_config.get('headers', {}),
            timeout=10
        )

class ServiceHealthMonitor:
    """Comprehensive service health monitoring with SLA tracking"""
    
    def __init__(self, services: List[str], alert_manager: AlertManager):
        self.services = services
        self.alert_manager = alert_manager
        self.health_history: Dict[str, List[ServiceHealth]] = {s: [] for s in services}
        self.sla_targets = {
            'uptime': 99.9,  # 99.9% uptime
            'response_time': 5.0,  # 5 second max response
            'error_rate': 1.0  # 1% max error rate
        }
        
        self.service_ports = {
            "market-data": "/tmp/trading_market-data.sock",
            "sentiment": "/tmp/trading_sentiment.sock",
            "prediction": "/tmp/trading_prediction.sock",
            "scheduler": "/tmp/trading_scheduler.sock",
            "paper-trading": "/tmp/trading_paper-trading.sock",
            "ml-model": "/tmp/trading_ml-model.sock"
        }
        
    async def check_all_services(self) -> Dict[str, ServiceHealth]:
        """Check health of all services"""
        health_results = {}
        
        tasks = []
        for service in self.services:
            task = self._check_service_health(service)
            tasks.append(task)
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            service = self.services[i]
            
            if isinstance(result, Exception):
                health = ServiceHealth(
                    service_name=service,
                    status="unhealthy",
                    uptime=0,
                    cpu_usage=0,
                    memory_usage=0,
                    response_time=999.0,
                    error_rate=100.0,
                    last_error=str(result),
                    dependencies_healthy=False,
                    sla_compliance=0.0
                )
            else:
                health = result
                
            health_results[service] = health
            self.health_history[service].append(health)
            
            # Keep only last 100 health checks per service
            if len(self.health_history[service]) > 100:
                self.health_history[service] = self.health_history[service][-100:]
                
            # Check for alerts
            self._check_health_alerts(health)
            
        return health_results
        
    async def _check_service_health(self, service: str) -> ServiceHealth:
        """Check health of individual service"""
        start_time = time.time()
        
        try:
            socket_path = self.service_ports.get(service)
            if not socket_path:
                raise ValueError(f"No socket path for {service}")
                
            # Connect and get health data
            reader, writer = await asyncio.wait_for(
                asyncio.open_unix_connection(socket_path),
                timeout=10.0
            )
            
            health_request = {
                'method': 'health',
                'params': {},
                'timestamp': time.time()
            }
            
            writer.write(json.dumps(health_request).encode())
            await writer.drain()
            
            response_data = await asyncio.wait_for(reader.read(8192), timeout=10.0)
            response = json.loads(response_data.decode())
            
            writer.close()
            await writer.wait_closed()
            
            response_time = time.time() - start_time
            
            if response.get('status') == 'success':
                health_data = response.get('result', {})
                
                # Calculate SLA compliance
                sla_compliance = self._calculate_sla_compliance(service, response_time, 0.0)
                
                return ServiceHealth(
                    service_name=service,
                    status=health_data.get('status', 'unknown'),
                    uptime=health_data.get('uptime', 0),
                    cpu_usage=health_data.get('cpu_usage', 0),
                    memory_usage=health_data.get('memory_usage', 0),
                    response_time=response_time,
                    error_rate=0.0,  # No error if we got here
                    last_error=None,
                    dependencies_healthy=True,
                    sla_compliance=sla_compliance
                )
            else:
                return ServiceHealth(
                    service_name=service,
                    status="unhealthy",
                    uptime=0,
                    cpu_usage=0,
                    memory_usage=0,
                    response_time=response_time,
                    error_rate=100.0,
                    last_error=response.get('error', 'Unknown error'),
                    dependencies_healthy=False,
                    sla_compliance=0.0
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            sla_compliance = self._calculate_sla_compliance(service, response_time, 100.0)
            
            return ServiceHealth(
                service_name=service,
                status="unhealthy",
                uptime=0,
                cpu_usage=0,
                memory_usage=0,
                response_time=response_time,
                error_rate=100.0,
                last_error=str(e),
                dependencies_healthy=False,
                sla_compliance=sla_compliance
            )
            
    def _calculate_sla_compliance(self, service: str, response_time: float, error_rate: float) -> float:
        """Calculate SLA compliance percentage"""
        # Get recent health history for this service
        recent_checks = self.health_history[service][-20:]  # Last 20 checks
        
        if not recent_checks:
            return 100.0 if error_rate == 0 else 0.0
            
        # Calculate uptime percentage
        healthy_checks = sum(1 for h in recent_checks if h.status == "healthy")
        uptime_percentage = (healthy_checks / len(recent_checks)) * 100
        
        # Calculate average response time
        avg_response_time = statistics.mean([h.response_time for h in recent_checks])
        response_time_score = 100.0 if avg_response_time <= self.sla_targets['response_time'] else 0.0
        
        # Calculate error rate score
        avg_error_rate = statistics.mean([h.error_rate for h in recent_checks])
        error_rate_score = 100.0 if avg_error_rate <= self.sla_targets['error_rate'] else 0.0
        
        # Overall SLA compliance (weighted average)
        overall_sla = (uptime_percentage * 0.5 + response_time_score * 0.3 + error_rate_score * 0.2)
        
        return min(100.0, max(0.0, overall_sla))
        
    def _check_health_alerts(self, health: ServiceHealth):
        """Check if health metrics trigger alerts"""
        service = health.service_name
        
        # Critical alerts
        if health.status != "healthy":
            self.alert_manager.create_alert(
                alert_type="service_down",
                service=service,
                severity="critical",
                condition="status != healthy",
                threshold=1.0,
                current_value=0.0,
                message=f"Service {service} is {health.status}: {health.last_error}"
            )
            
        # Response time alerts
        if health.response_time > self.sla_targets['response_time']:
            self.alert_manager.create_alert(
                alert_type="slow_response",
                service=service,
                severity="warning",
                condition=f"response_time > {self.sla_targets['response_time']}s",
                threshold=self.sla_targets['response_time'],
                current_value=health.response_time,
                message=f"Service {service} response time is {health.response_time:.2f}s (threshold: {self.sla_targets['response_time']}s)"
            )
            
        # Error rate alerts
        if health.error_rate > self.sla_targets['error_rate']:
            self.alert_manager.create_alert(
                alert_type="high_error_rate",
                service=service,
                severity="warning",
                condition=f"error_rate > {self.sla_targets['error_rate']}%",
                threshold=self.sla_targets['error_rate'],
                current_value=health.error_rate,
                message=f"Service {service} error rate is {health.error_rate:.1f}% (threshold: {self.sla_targets['error_rate']}%)"
            )
            
        # SLA compliance alerts
        if health.sla_compliance < 95.0:
            self.alert_manager.create_alert(
                alert_type="sla_violation",
                service=service,
                severity="critical" if health.sla_compliance < 90.0 else "warning",
                condition="sla_compliance < 95%",
                threshold=95.0,
                current_value=health.sla_compliance,
                message=f"Service {service} SLA compliance is {health.sla_compliance:.1f}% (threshold: 95%)"
            )

class MonitoringService(BaseService):
    """Main monitoring and observability service"""
    
    def __init__(self):
        super().__init__("monitoring")
        
        # Initialize components
        self.metrics_collector = MetricsCollector()
        
        # Load monitoring configuration
        self.config = self._load_monitoring_config()
        
        self.alert_manager = AlertManager(self.config.get('alerts', {}))
        
        self.services_to_monitor = [
            "market-data", "sentiment", "prediction", 
            "scheduler", "paper-trading", "ml-model"
        ]
        
        self.health_monitor = ServiceHealthMonitor(self.services_to_monitor, self.alert_manager)
        
        # Monitoring intervals (seconds)
        self.health_check_interval = 30
        self.metrics_collection_interval = 60
        self.system_metrics_interval = 30
        
        # Register handlers
        self.register_handler("get_service_health", self.get_service_health)
        self.register_handler("get_metrics", self.get_metrics_data)
        self.register_handler("get_alerts", self.get_active_alerts)
        self.register_handler("resolve_alert", self.resolve_alert)
        self.register_handler("get_dashboard_data", self.get_dashboard_data)
        self.register_handler("get_sla_report", self.get_sla_report)
        
        # Start background monitoring
        asyncio.create_task(self._start_monitoring_loops())
        
    def _load_monitoring_config(self) -> Dict[str, Any]:
        """Load monitoring configuration"""
        config_path = "config/monitoring.json"
        
        default_config = {
            "alerts": {
                "email": {
                    "enabled": False,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "from_email": "",
                    "to_emails": [],
                    "username": "",
                    "password": ""
                },
                "webhook": {
                    "enabled": False,
                    "url": "",
                    "headers": {}
                }
            },
            "metrics": {
                "retention_days": 7,
                "aggregation_intervals": [300, 3600, 86400]  # 5min, 1hour, 1day
            }
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
        except Exception as e:
            self.logger.warning(f"Failed to load monitoring config: {e}")
            
        return default_config
        
    async def _start_monitoring_loops(self):
        """Start background monitoring loops"""
        # Wait a bit for service to fully initialize
        await asyncio.sleep(5)
        
        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._health_monitoring_loop()),
            asyncio.create_task(self._metrics_collection_loop()),
            asyncio.create_task(self._system_monitoring_loop())
        ]
        
        # Wait for any task to complete (they shouldn't unless there's an error)
        await asyncio.gather(*tasks, return_exceptions=True)
        
    async def _health_monitoring_loop(self):
        """Continuous health monitoring loop"""
        while self.running:
            try:
                health_results = await self.health_monitor.check_all_services()
                
                # Record health metrics
                for service, health in health_results.items():
                    timestamp = time.time()
                    
                    # Record various health metrics
                    health_metrics = [
                        MetricPoint(timestamp, service, "uptime", health.uptime),
                        MetricPoint(timestamp, service, "response_time", health.response_time),
                        MetricPoint(timestamp, service, "error_rate", health.error_rate),
                        MetricPoint(timestamp, service, "sla_compliance", health.sla_compliance),
                        MetricPoint(timestamp, service, "memory_usage", health.memory_usage),
                        MetricPoint(timestamp, service, "cpu_usage", health.cpu_usage),
                        MetricPoint(timestamp, service, "status", 1.0 if health.status == "healthy" else 0.0)
                    ]
                    
                    for metric in health_metrics:
                        self.metrics_collector.record_metric(metric)
                        
                self.logger.info(f"Health check completed for {len(health_results)} services")
                
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                
            await asyncio.sleep(self.health_check_interval)
            
    async def _metrics_collection_loop(self):
        """Collect custom business metrics"""
        while self.running:
            try:
                timestamp = time.time()
                
                # Collect prediction metrics
                try:
                    buy_rate_result = await self.call_service("prediction", "get_buy_rate")
                    if buy_rate_result:
                        buy_rate = buy_rate_result.get('buy_rate', 0)
                        total_predictions = buy_rate_result.get('total_predictions', 0)
                        
                        self.metrics_collector.record_metric(
                            MetricPoint(timestamp, "prediction", "buy_rate", buy_rate)
                        )
                        self.metrics_collector.record_metric(
                            MetricPoint(timestamp, "prediction", "total_predictions", total_predictions)
                        )
                except Exception as e:
                    self.logger.warning(f"Failed to collect prediction metrics: {e}")
                    
                # Collect paper trading metrics
                try:
                    positions_result = await self.call_service("paper-trading", "get_positions")
                    if positions_result:
                        position_count = len(positions_result.get('positions', {}))
                        
                        self.metrics_collector.record_metric(
                            MetricPoint(timestamp, "paper-trading", "active_positions", position_count)
                        )
                except Exception as e:
                    self.logger.warning(f"Failed to collect trading metrics: {e}")
                    
                self.logger.debug("Business metrics collection completed")
                
            except Exception as e:
                self.logger.error(f"Metrics collection error: {e}")
                
            await asyncio.sleep(self.metrics_collection_interval)
            
    async def _system_monitoring_loop(self):
        """Monitor system-level metrics"""
        while self.running:
            try:
                timestamp = time.time()
                
                # Collect system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                system_metrics = [
                    MetricPoint(timestamp, "system", "cpu_percent", cpu_percent),
                    MetricPoint(timestamp, "system", "memory_percent", memory.percent),
                    MetricPoint(timestamp, "system", "memory_available_gb", memory.available / (1024**3)),
                    MetricPoint(timestamp, "system", "disk_percent", disk.percent),
                    MetricPoint(timestamp, "system", "disk_free_gb", disk.free / (1024**3))
                ]
                
                for metric in system_metrics:
                    self.metrics_collector.record_metric(metric)
                    
                # Check for system alerts
                if cpu_percent > 80:
                    self.alert_manager.create_alert(
                        alert_type="high_cpu",
                        service="system",
                        severity="warning",
                        condition="cpu > 80%",
                        threshold=80.0,
                        current_value=cpu_percent,
                        message=f"System CPU usage is {cpu_percent:.1f}%"
                    )
                    
                if memory.percent > 85:
                    self.alert_manager.create_alert(
                        alert_type="high_memory",
                        service="system",
                        severity="critical" if memory.percent > 95 else "warning",
                        condition="memory > 85%",
                        threshold=85.0,
                        current_value=memory.percent,
                        message=f"System memory usage is {memory.percent:.1f}%"
                    )
                    
                if disk.percent > 90:
                    self.alert_manager.create_alert(
                        alert_type="low_disk_space",
                        service="system",
                        severity="critical",
                        condition="disk > 90%",
                        threshold=90.0,
                        current_value=disk.percent,
                        message=f"System disk usage is {disk.percent:.1f}%"
                    )
                    
                self.logger.debug("System monitoring completed")
                
            except Exception as e:
                self.logger.error(f"System monitoring error: {e}")
                
            await asyncio.sleep(self.system_metrics_interval)
            
    async def get_service_health(self) -> Dict[str, Any]:
        """Get current health status of all services"""
        health_results = await self.health_monitor.check_all_services()
        
        return {
            "timestamp": time.time(),
            "services": {
                service: asdict(health) for service, health in health_results.items()
            },
            "summary": {
                "total_services": len(health_results),
                "healthy_services": sum(1 for h in health_results.values() if h.status == "healthy"),
                "unhealthy_services": sum(1 for h in health_results.values() if h.status != "healthy"),
                "avg_response_time": statistics.mean([h.response_time for h in health_results.values()]),
                "avg_sla_compliance": statistics.mean([h.sla_compliance for h in health_results.values()])
            }
        }
        
    async def get_metrics_data(self, service: str = None, metric_name: str = None, 
                             hours: int = 1) -> Dict[str, Any]:
        """Get metrics data for specified timeframe"""
        end_time = time.time()
        start_time = end_time - (hours * 3600)
        
        metrics = self.metrics_collector.get_metrics(
            service=service,
            metric_name=metric_name,
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )
        
        return {
            "start_time": start_time,
            "end_time": end_time,
            "hours": hours,
            "total_points": len(metrics),
            "metrics": metrics
        }
        
    async def get_active_alerts(self) -> Dict[str, Any]:
        """Get currently active alerts"""
        return {
            "timestamp": time.time(),
            "active_alerts": [asdict(alert) for alert in self.alert_manager.active_alerts.values()],
            "alert_count": len(self.alert_manager.active_alerts),
            "recent_history": [asdict(alert) for alert in self.alert_manager.alert_history[-20:]]
        }
        
    async def resolve_alert(self, alert_id: str) -> Dict[str, Any]:
        """Manually resolve an alert"""
        if alert_id in self.alert_manager.active_alerts:
            self.alert_manager.resolve_alert(alert_id)
            return {"status": "resolved", "alert_id": alert_id}
        else:
            return {"status": "not_found", "alert_id": alert_id}
            
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        # Get current health
        health_data = await self.get_service_health()
        
        # Get recent metrics (last hour)
        metrics_data = await self.get_metrics_data(hours=1)
        
        # Get active alerts
        alerts_data = await self.get_active_alerts()
        
        # Calculate additional dashboard metrics
        end_time = time.time()
        start_time = end_time - 3600  # Last hour
        
        # Get service performance trends
        service_trends = {}
        for service in self.services_to_monitor:
            response_times = self.metrics_collector.get_metrics(
                service=service,
                metric_name="response_time",
                start_time=start_time,
                end_time=end_time,
                limit=100
            )
            
            if response_times:
                avg_response = statistics.mean([m['value'] for m in response_times])
                service_trends[service] = {
                    "avg_response_time": avg_response,
                    "data_points": len(response_times)
                }
                
        return {
            "timestamp": time.time(),
            "health": health_data,
            "alerts": alerts_data,
            "service_trends": service_trends,
            "system_overview": {
                "total_services": len(self.services_to_monitor),
                "monitoring_uptime": time.time() - self.start_time,
                "total_metrics_collected": len(metrics_data.get('metrics', [])),
                "active_alert_count": alerts_data['alert_count']
            }
        }
        
    async def get_sla_report(self, days: int = 7) -> Dict[str, Any]:
        """Generate SLA compliance report"""
        end_time = time.time()
        start_time = end_time - (days * 86400)
        
        sla_report = {
            "report_period": {
                "start_time": start_time,
                "end_time": end_time,
                "days": days
            },
            "services": {},
            "overall": {}
        }
        
        # Calculate SLA metrics for each service
        total_compliance = []
        
        for service in self.services_to_monitor:
            # Get SLA compliance metrics
            compliance_metrics = self.metrics_collector.get_metrics(
                service=service,
                metric_name="sla_compliance",
                start_time=start_time,
                end_time=end_time,
                limit=10000
            )
            
            if compliance_metrics:
                avg_compliance = statistics.mean([m['value'] for m in compliance_metrics])
                min_compliance = min(m['value'] for m in compliance_metrics)
                max_compliance = max(m['value'] for m in compliance_metrics)
                
                sla_report["services"][service] = {
                    "avg_compliance": avg_compliance,
                    "min_compliance": min_compliance,
                    "max_compliance": max_compliance,
                    "data_points": len(compliance_metrics),
                    "sla_met": avg_compliance >= 99.0
                }
                
                total_compliance.append(avg_compliance)
            else:
                sla_report["services"][service] = {
                    "avg_compliance": 0.0,
                    "min_compliance": 0.0,
                    "max_compliance": 0.0,
                    "data_points": 0,
                    "sla_met": False
                }
                
        # Calculate overall SLA metrics
        if total_compliance:
            sla_report["overall"] = {
                "avg_compliance": statistics.mean(total_compliance),
                "services_meeting_sla": sum(1 for c in total_compliance if c >= 99.0),
                "total_services": len(total_compliance),
                "overall_sla_met": statistics.mean(total_compliance) >= 99.0
            }
        else:
            sla_report["overall"] = {
                "avg_compliance": 0.0,
                "services_meeting_sla": 0,
                "total_services": 0,
                "overall_sla_met": False
            }
            
        return sla_report

async def main():
    """Main monitoring service entry point"""
    monitoring_service = MonitoringService()
    
    try:
        await monitoring_service.start_server()
    except KeyboardInterrupt:
        monitoring_service.logger.info("Monitoring service shutting down...")
    except Exception as e:
        monitoring_service.logger.error(f"Monitoring service error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
