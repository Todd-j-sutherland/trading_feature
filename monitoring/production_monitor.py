#!/usr/bin/env python3
"""
Production Monitoring and Alerting System
Comprehensive monitoring for multi-region microservices trading system
"""

import asyncio
import json
import time
import smtplib
import ssl
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import psutil
import sqlite3
import subprocess
import redis
from dataclasses import dataclass, asdict
from enum import Enum

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertChannel(Enum):
    EMAIL = "email"
    LOG = "log"
    WEBHOOK = "webhook"
    SMS = "sms"

@dataclass
class Alert:
    timestamp: str
    severity: AlertSeverity
    service: str
    metric: str
    value: float
    threshold: float
    message: str
    region: str = "ASX"
    resolved: bool = False
    escalated: bool = False

@dataclass
class ServiceMetrics:
    service_name: str
    region: str
    cpu_usage: float
    memory_usage: float
    memory_limit: float
    uptime: float
    response_time: float
    error_rate: float
    request_count: int
    last_error: Optional[str]
    status: str
    timestamp: str

@dataclass
class SystemMetrics:
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    load_average: List[float]
    network_io: Dict[str, int]
    disk_io: Dict[str, int]
    temperature: Optional[float]

class ProductionMonitor:
    """Comprehensive production monitoring system"""
    
    def __init__(self, config_path: str = "monitoring_config.json"):
        self.config = self._load_config(config_path)
        self.alerts = []
        self.metrics_history = []
        self.active_alerts = {}
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, self.config.get("log_level", "INFO")),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.get("log_file", "monitoring.log")),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Services to monitor
        self.services = [
            "market-data",
            "sentiment",
            "prediction", 
            "paper-trading",
            "ml-model",
            "scheduler",
            "database"
        ]
        
        # Regions to monitor
        self.regions = ["ASX", "USA", "UK", "EU"]
        
        # Monitoring intervals
        self.system_check_interval = self.config.get("system_check_interval", 30)
        self.service_check_interval = self.config.get("service_check_interval", 60)
        self.database_check_interval = self.config.get("database_check_interval", 300)
        
        # Alert thresholds
        self.thresholds = self.config.get("thresholds", {
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "disk_usage": 90.0,
            "response_time": 5.0,
            "error_rate": 5.0,
            "service_downtime": 60.0
        })
        
        # Redis connection for metrics storage
        try:
            self.redis_client = redis.Redis(
                host=self.config.get("redis_host", "localhost"),
                port=self.config.get("redis_port", 6379),
                decode_responses=True
            )
            self.redis_client.ping()
        except Exception as e:
            self.logger.error(f"Redis connection failed: {e}")
            self.redis_client = None
        
        # Database for persistent storage
        self.db_path = self.config.get("metrics_db", "monitoring_metrics.db")
        self._init_database()

    def _load_config(self, config_path: str) -> Dict:
        """Load monitoring configuration"""
        default_config = {
            "log_level": "INFO",
            "log_file": "monitoring.log",
            "system_check_interval": 30,
            "service_check_interval": 60,
            "database_check_interval": 300,
            "alert_channels": ["log", "email"],
            "email": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "recipients": []
            },
            "webhooks": {
                "slack": "",
                "discord": "",
                "teams": ""
            },
            "thresholds": {
                "cpu_usage": 80.0,
                "memory_usage": 85.0,
                "disk_usage": 90.0,
                "response_time": 5.0,
                "error_rate": 5.0,
                "service_downtime": 60.0
            },
            "retention_days": 30
        }
        
        try:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
        except Exception as e:
            print(f"Warning: Could not load config file {config_path}: {e}")
            print("Using default configuration")
        
        return default_config

    def _init_database(self):
        """Initialize monitoring database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    cpu_percent REAL,
                    memory_percent REAL,
                    disk_usage_percent REAL,
                    load_average TEXT,
                    network_io TEXT,
                    disk_io TEXT,
                    temperature REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS service_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    service_name TEXT NOT NULL,
                    region TEXT NOT NULL,
                    cpu_usage REAL,
                    memory_usage REAL,
                    memory_limit REAL,
                    uptime REAL,
                    response_time REAL,
                    error_rate REAL,
                    request_count INTEGER,
                    last_error TEXT,
                    status TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    service TEXT NOT NULL,
                    metric TEXT NOT NULL,
                    value REAL,
                    threshold REAL,
                    message TEXT,
                    region TEXT,
                    resolved BOOLEAN DEFAULT FALSE,
                    escalated BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Create indices
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_service_metrics_timestamp ON service_metrics(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity)')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")

    async def start_monitoring(self):
        """Start all monitoring tasks"""
        self.logger.info("Starting production monitoring system")
        
        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._system_monitoring_loop()),
            asyncio.create_task(self._service_monitoring_loop()),
            asyncio.create_task(self._database_monitoring_loop()),
            asyncio.create_task(self._alert_processing_loop()),
            asyncio.create_task(self._cleanup_loop())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Monitoring error: {e}")
        finally:
            # Cancel all tasks
            for task in tasks:
                task.cancel()

    async def _system_monitoring_loop(self):
        """Monitor system-level metrics"""
        while True:
            try:
                metrics = await self._collect_system_metrics()
                await self._store_system_metrics(metrics)
                await self._check_system_alerts(metrics)
                
                await asyncio.sleep(self.system_check_interval)
                
            except Exception as e:
                self.logger.error(f"System monitoring error: {e}")
                await asyncio.sleep(10)

    async def _service_monitoring_loop(self):
        """Monitor microservices"""
        while True:
            try:
                for region in self.regions:
                    for service in self.services:
                        try:
                            metrics = await self._collect_service_metrics(service, region)
                            if metrics:
                                await self._store_service_metrics(metrics)
                                await self._check_service_alerts(metrics)
                        except Exception as e:
                            self.logger.error(f"Service monitoring error {service}@{region}: {e}")
                
                await asyncio.sleep(self.service_check_interval)
                
            except Exception as e:
                self.logger.error(f"Service monitoring loop error: {e}")
                await asyncio.sleep(10)

    async def _database_monitoring_loop(self):
        """Monitor database health and performance"""
        while True:
            try:
                await self._check_database_health()
                await asyncio.sleep(self.database_check_interval)
                
            except Exception as e:
                self.logger.error(f"Database monitoring error: {e}")
                await asyncio.sleep(30)

    async def _alert_processing_loop(self):
        """Process and escalate alerts"""
        while True:
            try:
                await self._process_alerts()
                await self._escalate_alerts()
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Alert processing error: {e}")
                await asyncio.sleep(10)

    async def _cleanup_loop(self):
        """Clean up old metrics and alerts"""
        while True:
            try:
                await self._cleanup_old_data()
                await asyncio.sleep(3600)  # Run hourly
                
            except Exception as e:
                self.logger.error(f"Cleanup error: {e}")
                await asyncio.sleep(300)

    async def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system-level metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage_percent = (disk.used / disk.total) * 100
            
            # Load average
            load_avg = list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            
            # Network I/O
            net_io = psutil.net_io_counters()
            network_io = {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            }
            
            # Disk I/O
            disk_io_counters = psutil.disk_io_counters()
            disk_io = {
                "read_bytes": disk_io_counters.read_bytes,
                "write_bytes": disk_io_counters.write_bytes,
                "read_count": disk_io_counters.read_count,
                "write_count": disk_io_counters.write_count
            }
            
            # Temperature (if available)
            temperature = None
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    # Get CPU temperature
                    for name, entries in temps.items():
                        if 'cpu' in name.lower() or 'core' in name.lower():
                            temperature = entries[0].current
                            break
            except:
                pass
            
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_usage_percent=disk_usage_percent,
                load_average=load_avg,
                network_io=network_io,
                disk_io=disk_io,
                temperature=temperature
            )
            
        except Exception as e:
            self.logger.error(f"System metrics collection failed: {e}")
            return None

    async def _collect_service_metrics(self, service: str, region: str) -> Optional[ServiceMetrics]:
        """Collect metrics for a specific service"""
        try:
            start_time = time.time()
            
            # Call service health endpoint
            reader, writer = await asyncio.wait_for(
                asyncio.open_unix_connection(f"/tmp/trading_{service}.sock"),
                timeout=5.0
            )
            
            request = {
                "method": "health",
                "params": {"region": region}
            }
            
            writer.write(json.dumps(request).encode())
            await writer.drain()
            
            response_data = await asyncio.wait_for(reader.read(8192), timeout=10.0)
            response = json.loads(response_data.decode())
            
            writer.close()
            await writer.wait_closed()
            
            response_time = time.time() - start_time
            
            if response.get("status") == "success":
                health_data = response["result"]
                
                return ServiceMetrics(
                    service_name=service,
                    region=region,
                    cpu_usage=health_data.get("cpu_usage", 0),
                    memory_usage=health_data.get("memory_usage", 0),
                    memory_limit=health_data.get("memory_limit", 0),
                    uptime=health_data.get("uptime", 0),
                    response_time=response_time,
                    error_rate=health_data.get("error_rate", 0),
                    request_count=health_data.get("request_count", 0),
                    last_error=health_data.get("last_error"),
                    status=health_data.get("status", "unknown"),
                    timestamp=datetime.now().isoformat()
                )
            else:
                # Service responded but with error
                return ServiceMetrics(
                    service_name=service,
                    region=region,
                    cpu_usage=0,
                    memory_usage=0,
                    memory_limit=0,
                    uptime=0,
                    response_time=response_time,
                    error_rate=100,
                    request_count=0,
                    last_error=response.get("error", "Unknown error"),
                    status="error",
                    timestamp=datetime.now().isoformat()
                )
                
        except asyncio.TimeoutError:
            return ServiceMetrics(
                service_name=service,
                region=region,
                cpu_usage=0,
                memory_usage=0,
                memory_limit=0,
                uptime=0,
                response_time=float('inf'),
                error_rate=100,
                request_count=0,
                last_error="Service timeout",
                status="timeout",
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            return ServiceMetrics(
                service_name=service,
                region=region,
                cpu_usage=0,
                memory_usage=0,
                memory_limit=0,
                uptime=0,
                response_time=float('inf'),
                error_rate=100,
                request_count=0,
                last_error=str(e),
                status="unreachable",
                timestamp=datetime.now().isoformat()
            )

    async def _store_system_metrics(self, metrics: SystemMetrics):
        """Store system metrics"""
        if not metrics:
            return
            
        try:
            # Store in Redis for real-time access
            if self.redis_client:
                key = f"system_metrics:{int(time.time())}"
                self.redis_client.setex(
                    key, 
                    3600,  # 1 hour TTL
                    json.dumps(asdict(metrics))
                )
            
            # Store in database for historical data
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO system_metrics 
                (timestamp, cpu_percent, memory_percent, disk_usage_percent, 
                 load_average, network_io, disk_io, temperature)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics.timestamp,
                metrics.cpu_percent,
                metrics.memory_percent,
                metrics.disk_usage_percent,
                json.dumps(metrics.load_average),
                json.dumps(metrics.network_io),
                json.dumps(metrics.disk_io),
                metrics.temperature
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to store system metrics: {e}")

    async def _store_service_metrics(self, metrics: ServiceMetrics):
        """Store service metrics"""
        try:
            # Store in Redis
            if self.redis_client:
                key = f"service_metrics:{metrics.service_name}:{metrics.region}:{int(time.time())}"
                self.redis_client.setex(
                    key,
                    3600,  # 1 hour TTL
                    json.dumps(asdict(metrics))
                )
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO service_metrics 
                (timestamp, service_name, region, cpu_usage, memory_usage, memory_limit,
                 uptime, response_time, error_rate, request_count, last_error, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics.timestamp,
                metrics.service_name,
                metrics.region,
                metrics.cpu_usage,
                metrics.memory_usage,
                metrics.memory_limit,
                metrics.uptime,
                metrics.response_time,
                metrics.error_rate,
                metrics.request_count,
                metrics.last_error,
                metrics.status
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to store service metrics: {e}")

    async def _check_system_alerts(self, metrics: SystemMetrics):
        """Check for system-level alerts"""
        if not metrics:
            return
            
        alerts_to_create = []
        
        # CPU usage alert
        if metrics.cpu_percent > self.thresholds["cpu_usage"]:
            alerts_to_create.append(Alert(
                timestamp=datetime.now().isoformat(),
                severity=AlertSeverity.HIGH if metrics.cpu_percent > 95 else AlertSeverity.MEDIUM,
                service="system",
                metric="cpu_usage",
                value=metrics.cpu_percent,
                threshold=self.thresholds["cpu_usage"],
                message=f"High CPU usage: {metrics.cpu_percent:.1f}%",
                region="system"
            ))
        
        # Memory usage alert
        if metrics.memory_percent > self.thresholds["memory_usage"]:
            alerts_to_create.append(Alert(
                timestamp=datetime.now().isoformat(),
                severity=AlertSeverity.HIGH if metrics.memory_percent > 95 else AlertSeverity.MEDIUM,
                service="system",
                metric="memory_usage",
                value=metrics.memory_percent,
                threshold=self.thresholds["memory_usage"],
                message=f"High memory usage: {metrics.memory_percent:.1f}%",
                region="system"
            ))
        
        # Disk usage alert
        if metrics.disk_usage_percent > self.thresholds["disk_usage"]:
            alerts_to_create.append(Alert(
                timestamp=datetime.now().isoformat(),
                severity=AlertSeverity.CRITICAL if metrics.disk_usage_percent > 95 else AlertSeverity.HIGH,
                service="system",
                metric="disk_usage",
                value=metrics.disk_usage_percent,
                threshold=self.thresholds["disk_usage"],
                message=f"High disk usage: {metrics.disk_usage_percent:.1f}%",
                region="system"
            ))
        
        # Process alerts
        for alert in alerts_to_create:
            await self._create_alert(alert)

    async def _check_service_alerts(self, metrics: ServiceMetrics):
        """Check for service-level alerts"""
        alerts_to_create = []
        
        # Service down alert
        if metrics.status in ["unreachable", "timeout", "error"]:
            alerts_to_create.append(Alert(
                timestamp=datetime.now().isoformat(),
                severity=AlertSeverity.CRITICAL,
                service=metrics.service_name,
                metric="service_status",
                value=0,
                threshold=1,
                message=f"Service {metrics.service_name}@{metrics.region} is {metrics.status}: {metrics.last_error}",
                region=metrics.region
            ))
        
        # High response time alert
        if metrics.response_time > self.thresholds["response_time"]:
            alerts_to_create.append(Alert(
                timestamp=datetime.now().isoformat(),
                severity=AlertSeverity.MEDIUM,
                service=metrics.service_name,
                metric="response_time",
                value=metrics.response_time,
                threshold=self.thresholds["response_time"],
                message=f"High response time for {metrics.service_name}@{metrics.region}: {metrics.response_time:.2f}s",
                region=metrics.region
            ))
        
        # High error rate alert
        if metrics.error_rate > self.thresholds["error_rate"]:
            alerts_to_create.append(Alert(
                timestamp=datetime.now().isoformat(),
                severity=AlertSeverity.HIGH,
                service=metrics.service_name,
                metric="error_rate",
                value=metrics.error_rate,
                threshold=self.thresholds["error_rate"],
                message=f"High error rate for {metrics.service_name}@{metrics.region}: {metrics.error_rate:.1f}%",
                region=metrics.region
            ))
        
        # Process alerts
        for alert in alerts_to_create:
            await self._create_alert(alert)

    async def _create_alert(self, alert: Alert):
        """Create and store alert"""
        try:
            # Check if similar alert already exists
            alert_key = f"{alert.service}:{alert.metric}:{alert.region}"
            
            if alert_key in self.active_alerts:
                # Update existing alert
                existing_alert = self.active_alerts[alert_key]
                existing_alert.value = alert.value
                existing_alert.timestamp = alert.timestamp
                existing_alert.message = alert.message
            else:
                # Create new alert
                self.active_alerts[alert_key] = alert
                self.alerts.append(alert)
                
                # Store in database
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO alerts 
                    (timestamp, severity, service, metric, value, threshold, message, region)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    alert.timestamp,
                    alert.severity.value,
                    alert.service,
                    alert.metric,
                    alert.value,
                    alert.threshold,
                    alert.message,
                    alert.region
                ))
                
                conn.commit()
                conn.close()
                
                # Send alert notification
                await self._send_alert_notification(alert)
                
                self.logger.warning(f"ALERT: {alert.severity.value.upper()} - {alert.message}")
                
        except Exception as e:
            self.logger.error(f"Failed to create alert: {e}")

    async def _send_alert_notification(self, alert: Alert):
        """Send alert notification through configured channels"""
        try:
            channels = self.config.get("alert_channels", ["log"])
            
            for channel in channels:
                if channel == "email":
                    await self._send_email_alert(alert)
                elif channel == "webhook":
                    await self._send_webhook_alert(alert)
                elif channel == "log":
                    # Already logged in _create_alert
                    pass
                    
        except Exception as e:
            self.logger.error(f"Failed to send alert notification: {e}")

    async def _send_email_alert(self, alert: Alert):
        """Send email alert"""
        try:
            email_config = self.config.get("email", {})
            if not email_config.get("username") or not email_config.get("recipients"):
                return
            
            msg = MimeMultipart()
            msg['From'] = email_config["username"]
            msg['To'] = ", ".join(email_config["recipients"])
            msg['Subject'] = f"Trading System Alert - {alert.severity.value.upper()}"
            
            body = f"""
Trading System Alert

Severity: {alert.severity.value.upper()}
Service: {alert.service}
Region: {alert.region}
Metric: {alert.metric}
Value: {alert.value}
Threshold: {alert.threshold}
Message: {alert.message}
Timestamp: {alert.timestamp}

Please investigate this issue immediately.
"""
            
            msg.attach(MimeText(body, 'plain'))
            
            context = ssl.create_default_context()
            with smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"]) as server:
                server.starttls(context=context)
                server.login(email_config["username"], email_config["password"])
                server.send_message(msg)
                
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")

    async def _send_webhook_alert(self, alert: Alert):
        """Send webhook alert (Slack, Discord, Teams)"""
        # Implementation for webhook alerts
        # This would use aiohttp to send HTTP requests to webhook URLs
        pass

    async def _check_database_health(self):
        """Check database health and performance"""
        try:
            databases = [
                "trading_predictions.db",
                "paper_trading.db",
                "predictions.db",
                "data/enhanced_outcomes.db",
                "data/ig_markets_paper_trades.db"
            ]
            
            for db_file in databases:
                db_path = Path(db_file)
                if db_path.exists():
                    # Check database accessibility
                    start_time = time.time()
                    conn = sqlite3.connect(str(db_path))
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    conn.close()
                    response_time = time.time() - start_time
                    
                    # Check database size
                    db_size_mb = db_path.stat().st_size / (1024 * 1024)
                    
                    # Alert on slow database response
                    if response_time > 1.0:
                        await self._create_alert(Alert(
                            timestamp=datetime.now().isoformat(),
                            severity=AlertSeverity.MEDIUM,
                            service="database",
                            metric="response_time",
                            value=response_time,
                            threshold=1.0,
                            message=f"Slow database response for {db_file}: {response_time:.2f}s",
                            region="system"
                        ))
                    
                    # Alert on large database size
                    if db_size_mb > 1000:  # 1GB
                        await self._create_alert(Alert(
                            timestamp=datetime.now().isoformat(),
                            severity=AlertSeverity.MEDIUM,
                            service="database",
                            metric="size",
                            value=db_size_mb,
                            threshold=1000,
                            message=f"Large database size for {db_file}: {db_size_mb:.1f}MB",
                            region="system"
                        ))
                        
        except Exception as e:
            await self._create_alert(Alert(
                timestamp=datetime.now().isoformat(),
                severity=AlertSeverity.HIGH,
                service="database",
                metric="health_check",
                value=0,
                threshold=1,
                message=f"Database health check failed: {e}",
                region="system"
            ))

    async def _process_alerts(self):
        """Process and manage active alerts"""
        try:
            current_time = datetime.now()
            resolved_alerts = []
            
            for alert_key, alert in self.active_alerts.items():
                # Check if alert should be auto-resolved
                alert_time = datetime.fromisoformat(alert.timestamp)
                age_minutes = (current_time - alert_time).total_seconds() / 60
                
                # Auto-resolve alerts older than 30 minutes if conditions improved
                if age_minutes > 30:
                    if await self._check_alert_resolution(alert):
                        alert.resolved = True
                        resolved_alerts.append(alert_key)
                        
                        # Update in database
                        conn = sqlite3.connect(self.db_path)
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE alerts SET resolved = TRUE WHERE service = ? AND metric = ? AND region = ? AND timestamp = ?",
                            (alert.service, alert.metric, alert.region, alert.timestamp)
                        )
                        conn.commit()
                        conn.close()
                        
                        self.logger.info(f"Alert resolved: {alert.message}")
            
            # Remove resolved alerts from active alerts
            for alert_key in resolved_alerts:
                del self.active_alerts[alert_key]
                
        except Exception as e:
            self.logger.error(f"Alert processing error: {e}")

    async def _check_alert_resolution(self, alert: Alert) -> bool:
        """Check if an alert condition has been resolved"""
        try:
            if alert.service == "system":
                # Check current system metrics
                current_metrics = await self._collect_system_metrics()
                if not current_metrics:
                    return False
                
                if alert.metric == "cpu_usage":
                    return current_metrics.cpu_percent < alert.threshold
                elif alert.metric == "memory_usage":
                    return current_metrics.memory_percent < alert.threshold
                elif alert.metric == "disk_usage":
                    return current_metrics.disk_usage_percent < alert.threshold
            else:
                # Check current service metrics
                current_metrics = await self._collect_service_metrics(alert.service, alert.region)
                if not current_metrics:
                    return False
                
                if alert.metric == "service_status":
                    return current_metrics.status == "healthy"
                elif alert.metric == "response_time":
                    return current_metrics.response_time < alert.threshold
                elif alert.metric == "error_rate":
                    return current_metrics.error_rate < alert.threshold
            
            return False
            
        except Exception as e:
            self.logger.error(f"Alert resolution check failed: {e}")
            return False

    async def _escalate_alerts(self):
        """Escalate critical alerts that haven't been resolved"""
        try:
            current_time = datetime.now()
            
            for alert in self.active_alerts.values():
                if alert.severity == AlertSeverity.CRITICAL and not alert.escalated:
                    alert_time = datetime.fromisoformat(alert.timestamp)
                    age_minutes = (current_time - alert_time).total_seconds() / 60
                    
                    # Escalate critical alerts after 15 minutes
                    if age_minutes > 15:
                        alert.escalated = True
                        
                        # Send escalation notification
                        escalation_alert = Alert(
                            timestamp=datetime.now().isoformat(),
                            severity=AlertSeverity.CRITICAL,
                            service=alert.service,
                            metric=alert.metric,
                            value=alert.value,
                            threshold=alert.threshold,
                            message=f"ESCALATED: {alert.message} (unresolved for {age_minutes:.0f} minutes)",
                            region=alert.region,
                            escalated=True
                        )
                        
                        await self._send_alert_notification(escalation_alert)
                        
        except Exception as e:
            self.logger.error(f"Alert escalation error: {e}")

    async def _cleanup_old_data(self):
        """Clean up old metrics and alerts"""
        try:
            retention_days = self.config.get("retention_days", 30)
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            cutoff_str = cutoff_date.isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clean up old metrics
            cursor.execute("DELETE FROM system_metrics WHERE timestamp < ?", (cutoff_str,))
            cursor.execute("DELETE FROM service_metrics WHERE timestamp < ?", (cutoff_str,))
            
            # Clean up resolved alerts older than retention period
            cursor.execute("DELETE FROM alerts WHERE timestamp < ? AND resolved = TRUE", (cutoff_str,))
            
            conn.commit()
            conn.close()
            
            # Clean up Redis keys
            if self.redis_client:
                # This would require a more sophisticated cleanup for Redis
                pass
                
            self.logger.info(f"Cleaned up data older than {retention_days} days")
            
        except Exception as e:
            self.logger.error(f"Data cleanup error: {e}")

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        try:
            # Get recent metrics
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # System metrics summary
            cursor.execute('''
                SELECT AVG(cpu_percent), AVG(memory_percent), AVG(disk_usage_percent)
                FROM system_metrics 
                WHERE timestamp > datetime('now', '-1 hour')
            ''')
            system_avg = cursor.fetchone()
            
            # Service status summary
            cursor.execute('''
                SELECT service_name, region, status, COUNT(*) as count
                FROM service_metrics 
                WHERE timestamp > datetime('now', '-1 hour')
                GROUP BY service_name, region, status
            ''')
            service_status = cursor.fetchall()
            
            # Recent alerts
            cursor.execute('''
                SELECT severity, COUNT(*) as count
                FROM alerts 
                WHERE timestamp > datetime('now', '-24 hours') AND resolved = FALSE
                GROUP BY severity
            ''')
            alert_counts = cursor.fetchall()
            
            conn.close()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "system_summary": {
                    "avg_cpu": system_avg[0] if system_avg[0] else 0,
                    "avg_memory": system_avg[1] if system_avg[1] else 0,
                    "avg_disk": system_avg[2] if system_avg[2] else 0
                },
                "service_status": [
                    {
                        "service": row[0],
                        "region": row[1], 
                        "status": row[2],
                        "count": row[3]
                    } for row in service_status
                ],
                "alert_summary": {
                    row[0]: row[1] for row in alert_counts
                },
                "active_alerts": len(self.active_alerts),
                "total_services": len(self.services) * len(self.regions)
            }
            
        except Exception as e:
            self.logger.error(f"Dashboard data error: {e}")
            return {"error": str(e)}

async def main():
    """Main monitoring function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Production monitoring system")
    parser.add_argument("--config", default="monitoring_config.json")
    parser.add_argument("--dashboard", action="store_true", help="Show dashboard data")
    
    args = parser.parse_args()
    
    monitor = ProductionMonitor(args.config)
    
    if args.dashboard:
        # Show dashboard data and exit
        dashboard_data = monitor.get_dashboard_data()
        print(json.dumps(dashboard_data, indent=2))
        return
    
    # Start monitoring
    await monitor.start_monitoring()

if __name__ == "__main__":
    asyncio.run(main())
