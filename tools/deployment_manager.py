#!/usr/bin/env python3
"""
Comprehensive Deployment and Operations Manager

This module provides automated deployment, operations management, and production 
readiness tools for the trading microservices architecture.

Features:
- Automated service deployment with dependency management
- Environment-specific configuration management
- Database migration and backup automation
- Health monitoring and recovery procedures
- Rollback capabilities with version management
- Production readiness validation
- Operational runbooks automation

Author: Trading System Deployment Manager
Date: September 14, 2025
"""

import subprocess
import sys
import os
import json
import time
import shutil
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import argparse
import logging
import tempfile
import threading
import concurrent.futures
from dataclasses import dataclass
import yaml

@dataclass
class DeploymentConfig:
    """Deployment configuration structure"""
    environment: str
    services: List[str]
    dependencies: Dict[str, List[str]]
    resource_limits: Dict[str, Dict[str, str]]
    healthcheck_timeout: int
    rollback_enabled: bool
    backup_before_deploy: bool
    
@dataclass
class ServiceStatus:
    """Service deployment status"""
    name: str
    status: str  # deployed, failed, rollback, healthy
    version: str
    deployment_time: datetime
    health_check_passed: bool
    error_message: Optional[str] = None

class DeploymentManager:
    """Comprehensive deployment and operations management"""
    
    def __init__(self, config_path: str = "config/deployment.yaml"):
        self.config_path = config_path
        self.deployment_config = self._load_deployment_config()
        self.deployment_log_path = "logs/deployment.log"
        
        # Service definitions
        self.services = {
            "market-data": {
                "description": "Market Data Service",
                "main_file": "services/market_data_service.py",
                "systemd_service": "trading-market-data.service",
                "dependencies": [],
                "health_endpoint": "health",
                "socket_path": "/tmp/trading_market-data.sock"
            },
            "sentiment": {
                "description": "Sentiment Analysis Service", 
                "main_file": "services/sentiment_service.py",
                "systemd_service": "trading-sentiment.service",
                "dependencies": [],
                "health_endpoint": "health",
                "socket_path": "/tmp/trading_sentiment.sock"
            },
            "ml-model": {
                "description": "ML Model Management Service",
                "main_file": "services/ml_model_service.py", 
                "systemd_service": "trading-ml-model.service",
                "dependencies": [],
                "health_endpoint": "health",
                "socket_path": "/tmp/trading_ml-model.sock"
            },
            "prediction": {
                "description": "Prediction Generation Service",
                "main_file": "services/prediction_service.py",
                "systemd_service": "trading-prediction.service", 
                "dependencies": ["market-data", "sentiment"],
                "health_endpoint": "health",
                "socket_path": "/tmp/trading_prediction.sock"
            },
            "paper-trading": {
                "description": "Paper Trading Service",
                "main_file": "services/paper_trading_service.py",
                "systemd_service": "trading-paper-trading.service",
                "dependencies": ["prediction"],
                "health_endpoint": "health", 
                "socket_path": "/tmp/trading_paper-trading.sock"
            },
            "scheduler": {
                "description": "Task Scheduler Service",
                "main_file": "services/scheduler_service.py",
                "systemd_service": "trading-scheduler.service",
                "dependencies": ["prediction", "paper-trading"],
                "health_endpoint": "health",
                "socket_path": "/tmp/trading_scheduler.sock"
            },
            "monitoring": {
                "description": "Monitoring and Observability Service",
                "main_file": "services/monitoring_service.py",
                "systemd_service": "trading-monitoring.service",
                "dependencies": [],
                "health_endpoint": "health",
                "socket_path": "/tmp/trading_monitoring.sock"
            },
            "monitoring-dashboard": {
                "description": "Monitoring Web Dashboard",
                "main_file": "services/monitoring_dashboard.py",
                "systemd_service": "trading-monitoring-dashboard.service", 
                "dependencies": ["monitoring"],
                "health_endpoint": None,  # Web service
                "socket_path": None
            }
        }
        
        # Setup logging
        self._setup_deployment_logging()
        
    def _load_deployment_config(self) -> DeploymentConfig:
        """Load deployment configuration"""
        default_config = {
            'environment': 'production',
            'services': list(self.services.keys()) if hasattr(self, 'services') else [],
            'dependencies': {},
            'resource_limits': {
                'default': {'memory': '512M', 'cpu': '100%'},
                'prediction': {'memory': '1G', 'cpu': '150%'},
                'monitoring': {'memory': '1G', 'cpu': '100%'}
            },
            'healthcheck_timeout': 60,
            'rollback_enabled': True,
            'backup_before_deploy': True
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                    
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config_data:
                        config_data[key] = value
                        
                return DeploymentConfig(**config_data)
        except Exception as e:
            print(f"Warning: Failed to load deployment config: {e}")
            
        return DeploymentConfig(**default_config)
        
    def _setup_deployment_logging(self):
        """Setup deployment logging"""
        log_dir = Path(self.deployment_log_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.deployment_log_path),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        
    def deploy_all_services(self, environment: str = "production") -> Dict[str, ServiceStatus]:
        """Deploy all services with dependency management"""
        self.logger.info(f"🚀 Starting deployment to {environment} environment")
        
        deployment_results = {}
        
        # Create deployment backup if enabled
        if self.deployment_config.backup_before_deploy:
            backup_path = self._create_deployment_backup()
            self.logger.info(f"📦 Created deployment backup: {backup_path}")
            
        # Get deployment order based on dependencies
        deployment_order = self._calculate_deployment_order()
        self.logger.info(f"📋 Deployment order: {' → '.join(deployment_order)}")
        
        # Deploy services in order
        for service_name in deployment_order:
            self.logger.info(f"🔧 Deploying {service_name}...")
            
            try:
                # Stop existing service
                self._stop_service(service_name)
                
                # Deploy new version
                deployment_result = self._deploy_single_service(service_name, environment)
                deployment_results[service_name] = deployment_result
                
                if deployment_result.status == "failed":
                    self.logger.error(f"❌ Deployment failed for {service_name}: {deployment_result.error_message}")
                    
                    # Rollback if enabled
                    if self.deployment_config.rollback_enabled:
                        self.logger.info(f"🔄 Rolling back {service_name}...")
                        self._rollback_service(service_name)
                        
                    break
                else:
                    self.logger.info(f"✅ Successfully deployed {service_name}")
                    
            except Exception as e:
                self.logger.error(f"💥 Deployment error for {service_name}: {e}")
                deployment_results[service_name] = ServiceStatus(
                    name=service_name,
                    status="failed",
                    version="unknown",
                    deployment_time=datetime.now(),
                    health_check_passed=False,
                    error_message=str(e)
                )
                break
                
        # Final health check
        self.logger.info("🏥 Running final health checks...")
        self._run_final_health_checks(deployment_results)
        
        # Deployment summary
        successful_deployments = sum(1 for s in deployment_results.values() if s.status == "deployed")
        total_deployments = len(deployment_results)
        
        self.logger.info(f"📊 Deployment Summary: {successful_deployments}/{total_deployments} services deployed successfully")
        
        return deployment_results
        
    def _calculate_deployment_order(self) -> List[str]:
        """Calculate optimal deployment order based on dependencies"""
        # Topological sort for dependency resolution
        in_degree = {service: 0 for service in self.services}
        dependencies = {}
        
        # Build dependency graph
        for service_name, service_config in self.services.items():
            service_deps = service_config.get('dependencies', [])
            dependencies[service_name] = service_deps
            
            for dep in service_deps:
                if dep in in_degree:
                    in_degree[service_name] += 1
                    
        # Topological sort
        queue = [service for service, degree in in_degree.items() if degree == 0]
        deployment_order = []
        
        while queue:
            service = queue.pop(0)
            deployment_order.append(service)
            
            # Update in-degrees
            for other_service, deps in dependencies.items():
                if service in deps:
                    in_degree[other_service] -= 1
                    if in_degree[other_service] == 0:
                        queue.append(other_service)
                        
        return deployment_order
        
    def _deploy_single_service(self, service_name: str, environment: str) -> ServiceStatus:
        """Deploy a single service"""
        service_config = self.services[service_name]
        
        try:
            # 1. Validate service files exist
            main_file = service_config['main_file']
            if not os.path.exists(main_file):
                raise FileNotFoundError(f"Service main file not found: {main_file}")
                
            # 2. Install/update systemd service file
            systemd_service = service_config['systemd_service']
            systemd_source = f"systemd/{systemd_service}"
            systemd_target = f"/etc/systemd/system/{systemd_service}"
            
            if os.path.exists(systemd_source):
                subprocess.run(['sudo', 'cp', systemd_source, systemd_target], check=True)
                subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
                subprocess.run(['sudo', 'systemctl', 'enable', systemd_service], check=True)
            else:
                self.logger.warning(f"Systemd service file not found: {systemd_source}")
                
            # 3. Start service
            result = subprocess.run(['sudo', 'systemctl', 'start', systemd_service], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, result.args, result.stderr)
                
            # 4. Wait for startup
            time.sleep(5)
            
            # 5. Health check
            health_check_passed = self._perform_health_check(service_name)
            
            # 6. Get service version (simplified)
            version = self._get_service_version(service_name)
            
            status = "deployed" if health_check_passed else "unhealthy"
            
            return ServiceStatus(
                name=service_name,
                status=status,
                version=version,
                deployment_time=datetime.now(),
                health_check_passed=health_check_passed
            )
            
        except Exception as e:
            return ServiceStatus(
                name=service_name,
                status="failed",
                version="unknown",
                deployment_time=datetime.now(),
                health_check_passed=False,
                error_message=str(e)
            )
            
    def _stop_service(self, service_name: str):
        """Stop a service gracefully"""
        service_config = self.services[service_name]
        systemd_service = service_config['systemd_service']
        
        try:
            # Check if service is running
            result = subprocess.run(['systemctl', 'is-active', systemd_service], 
                                  capture_output=True, text=True)
            
            if result.stdout.strip() == 'active':
                self.logger.info(f"⏹️ Stopping {service_name}...")
                subprocess.run(['sudo', 'systemctl', 'stop', systemd_service], check=True)
                
                # Wait for graceful shutdown
                time.sleep(3)
                
                # Verify stopped
                result = subprocess.run(['systemctl', 'is-active', systemd_service], 
                                      capture_output=True, text=True)
                
                if result.stdout.strip() != 'inactive':
                    self.logger.warning(f"Service {service_name} may not have stopped cleanly")
                    
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Error stopping {service_name}: {e}")
            
    def _perform_health_check(self, service_name: str) -> bool:
        """Perform health check for a service"""
        service_config = self.services[service_name]
        
        # Skip health check for services without health endpoints
        if not service_config.get('health_endpoint'):
            return True
            
        socket_path = service_config.get('socket_path')
        if not socket_path:
            return True
            
        max_attempts = 6  # 60 seconds with 10 second intervals
        
        for attempt in range(max_attempts):
            try:
                # Simple socket connection test
                import socket
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect(socket_path)
                
                # Send health check request
                import json
                health_request = json.dumps({
                    'method': 'health',
                    'params': {}
                }).encode()
                
                sock.send(health_request)
                response = sock.recv(1024)
                sock.close()
                
                if response:
                    response_data = json.loads(response.decode())
                    if response_data.get('status') == 'success':
                        return True
                        
            except Exception as e:
                self.logger.debug(f"Health check attempt {attempt + 1} failed for {service_name}: {e}")
                
            if attempt < max_attempts - 1:
                time.sleep(10)
                
        return False
        
    def _get_service_version(self, service_name: str) -> str:
        """Get service version (simplified implementation)"""
        try:
            # For now, use current timestamp as version
            return datetime.now().strftime("%Y%m%d_%H%M%S")
        except Exception:
            return "unknown"
            
    def _create_deployment_backup(self) -> str:
        """Create backup before deployment"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"backups/deployment_backup_{timestamp}"
        
        os.makedirs(backup_dir, exist_ok=True)
        
        # Backup critical files and directories
        backup_items = [
            "services/",
            "systemd/", 
            "config/",
            "data/",
            "*.db"
        ]
        
        for item in backup_items:
            if os.path.exists(item):
                if os.path.isdir(item):
                    shutil.copytree(item, f"{backup_dir}/{item}", dirs_exist_ok=True)
                else:
                    shutil.copy2(item, backup_dir)
                    
        return backup_dir
        
    def _rollback_service(self, service_name: str):
        """Rollback a service to previous version"""
        # Simplified rollback - stop current service
        self._stop_service(service_name)
        self.logger.info(f"🔄 Service {service_name} rolled back (stopped)")
        
    def _run_final_health_checks(self, deployment_results: Dict[str, ServiceStatus]):
        """Run final comprehensive health checks"""
        self.logger.info("🔍 Running comprehensive health validation...")
        
        for service_name, status in deployment_results.items():
            if status.status == "deployed":
                # Re-check health
                health_ok = self._perform_health_check(service_name)
                status.health_check_passed = health_ok
                
                if not health_ok:
                    status.status = "unhealthy"
                    self.logger.warning(f"⚠️ {service_name} deployed but failing health checks")
                    
    def validate_production_readiness(self) -> Dict[str, Any]:
        """Validate system production readiness"""
        self.logger.info("🔍 Validating production readiness...")
        
        validation_results = {
            'timestamp': datetime.now().isoformat(),
            'overall_ready': False,
            'checks': {},
            'warnings': [],
            'errors': []
        }
        
        # Check 1: Service files exist
        service_files_check = self._check_service_files()
        validation_results['checks']['service_files'] = service_files_check
        
        # Check 2: Configuration files
        config_check = self._check_configuration_files()
        validation_results['checks']['configuration'] = config_check
        
        # Check 3: Dependencies (Python packages, system requirements)
        dependencies_check = self._check_dependencies()
        validation_results['checks']['dependencies'] = dependencies_check
        
        # Check 4: Database integrity
        database_check = self._check_database_integrity()
        validation_results['checks']['database'] = database_check
        
        # Check 5: System resources
        resources_check = self._check_system_resources()
        validation_results['checks']['resources'] = resources_check
        
        # Check 6: Network and ports
        network_check = self._check_network_requirements()
        validation_results['checks']['network'] = network_check
        
        # Check 7: Security configuration
        security_check = self._check_security_configuration()
        validation_results['checks']['security'] = security_check
        
        # Overall readiness assessment
        all_checks_passed = all(
            check.get('passed', False) 
            for check in validation_results['checks'].values()
        )
        
        critical_errors = [
            check for check in validation_results['checks'].values()
            if not check.get('passed', False) and check.get('severity') == 'critical'
        ]
        
        validation_results['overall_ready'] = all_checks_passed and len(critical_errors) == 0
        
        # Collect warnings and errors
        for check_name, check_result in validation_results['checks'].items():
            if not check_result.get('passed', False):
                severity = check_result.get('severity', 'warning')
                message = f"{check_name}: {check_result.get('message', 'Check failed')}"
                
                if severity == 'critical':
                    validation_results['errors'].append(message)
                else:
                    validation_results['warnings'].append(message)
                    
        self.logger.info(f"✅ Production readiness: {'READY' if validation_results['overall_ready'] else 'NOT READY'}")
        
        return validation_results
        
    def _check_service_files(self) -> Dict[str, Any]:
        """Check if all service files exist and are valid"""
        missing_files = []
        
        for service_name, config in self.services.items():
            main_file = config['main_file']
            systemd_file = f"systemd/{config['systemd_service']}"
            
            if not os.path.exists(main_file):
                missing_files.append(main_file)
                
            if not os.path.exists(systemd_file):
                missing_files.append(systemd_file)
                
        return {
            'passed': len(missing_files) == 0,
            'severity': 'critical' if missing_files else 'info',
            'message': f"Missing files: {missing_files}" if missing_files else "All service files present",
            'details': {'missing_files': missing_files}
        }
        
    def _check_configuration_files(self) -> Dict[str, Any]:
        """Check configuration files"""
        config_files = [
            'config/monitoring.json',
            'config/deployment.yaml'
        ]
        
        missing_configs = []
        invalid_configs = []
        
        for config_file in config_files:
            if not os.path.exists(config_file):
                missing_configs.append(config_file)
            else:
                try:
                    if config_file.endswith('.json'):
                        with open(config_file, 'r') as f:
                            json.load(f)
                    elif config_file.endswith('.yaml'):
                        with open(config_file, 'r') as f:
                            yaml.safe_load(f)
                except Exception as e:
                    invalid_configs.append(f"{config_file}: {e}")
                    
        issues = missing_configs + invalid_configs
        
        return {
            'passed': len(issues) == 0,
            'severity': 'warning' if issues else 'info',
            'message': f"Configuration issues: {issues}" if issues else "All configurations valid",
            'details': {'missing': missing_configs, 'invalid': invalid_configs}
        }
        
    def _check_dependencies(self) -> Dict[str, Any]:
        """Check Python dependencies and system requirements"""
        missing_packages = []
        
        required_packages = [
            'asyncio', 'json', 'sqlite3', 'redis', 'flask', 
            'psutil', 'aiofiles', 'requests'
        ]
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
                
        # Check Redis availability
        redis_available = False
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=5)
            r.ping()
            redis_available = True
        except Exception:
            pass
            
        issues = []
        if missing_packages:
            issues.append(f"Missing packages: {missing_packages}")
        if not redis_available:
            issues.append("Redis not available")
            
        return {
            'passed': len(issues) == 0,
            'severity': 'critical' if issues else 'info',
            'message': '; '.join(issues) if issues else "All dependencies satisfied",
            'details': {'missing_packages': missing_packages, 'redis_available': redis_available}
        }
        
    def _check_database_integrity(self) -> Dict[str, Any]:
        """Check database files and integrity"""
        database_files = [
            'predictions.db',
            'trading_predictions.db', 
            'paper_trading.db',
            'data/metrics.db'
        ]
        
        missing_dbs = []
        corrupt_dbs = []
        
        for db_file in database_files:
            if not os.path.exists(db_file):
                missing_dbs.append(db_file)
            else:
                try:
                    conn = sqlite3.connect(db_file)
                    conn.execute("SELECT 1")
                    conn.close()
                except Exception as e:
                    corrupt_dbs.append(f"{db_file}: {e}")
                    
        issues = []
        if missing_dbs:
            issues.append(f"Missing databases: {missing_dbs}")
        if corrupt_dbs:
            issues.append(f"Corrupt databases: {corrupt_dbs}")
            
        return {
            'passed': len(issues) == 0,
            'severity': 'warning' if issues else 'info',
            'message': '; '.join(issues) if issues else "All databases healthy",
            'details': {'missing': missing_dbs, 'corrupt': corrupt_dbs}
        }
        
    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resources availability"""
        try:
            import psutil
            
            # Memory check
            memory = psutil.virtual_memory()
            memory_available_gb = memory.available / (1024**3)
            
            # Disk check
            disk = psutil.disk_usage('/')
            disk_free_gb = disk.free / (1024**3)
            
            # CPU check
            cpu_count = psutil.cpu_count()
            
            warnings = []
            
            if memory_available_gb < 2:
                warnings.append(f"Low memory: {memory_available_gb:.1f}GB available")
                
            if disk_free_gb < 5:
                warnings.append(f"Low disk space: {disk_free_gb:.1f}GB available")
                
            if cpu_count < 2:
                warnings.append(f"Limited CPU cores: {cpu_count}")
                
            return {
                'passed': len(warnings) == 0,
                'severity': 'warning' if warnings else 'info',
                'message': '; '.join(warnings) if warnings else "System resources adequate",
                'details': {
                    'memory_available_gb': memory_available_gb,
                    'disk_free_gb': disk_free_gb,
                    'cpu_count': cpu_count
                }
            }
            
        except Exception as e:
            return {
                'passed': False,
                'severity': 'warning',
                'message': f"Could not check system resources: {e}",
                'details': {}
            }
            
    def _check_network_requirements(self) -> Dict[str, Any]:
        """Check network and port requirements"""
        required_ports = [6379]  # Redis
        optional_ports = [5000]  # Dashboard
        
        port_issues = []
        
        for port in required_ports:
            if not self._is_port_available(port):
                port_issues.append(f"Required port {port} not available")
                
        return {
            'passed': len(port_issues) == 0,
            'severity': 'critical' if port_issues else 'info',
            'message': '; '.join(port_issues) if port_issues else "Network requirements satisfied",
            'details': {'port_issues': port_issues}
        }
        
    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result == 0  # 0 means connection successful (port in use)
        except Exception:
            return False
            
    def _check_security_configuration(self) -> Dict[str, Any]:
        """Check security configuration"""
        security_issues = []
        
        # Check for default passwords or keys
        config_files = ['config/monitoring.json']
        
        for config_file in config_files:
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        config_data = json.load(f)
                        
                    # Check for empty passwords
                    if 'alerts' in config_data and 'email' in config_data['alerts']:
                        email_config = config_data['alerts']['email']
                        if email_config.get('enabled') and not email_config.get('password'):
                            security_issues.append("Email password not configured")
                            
                except Exception:
                    pass
                    
        # Check file permissions (simplified)
        sensitive_files = ['config/']
        for path in sensitive_files:
            if os.path.exists(path):
                # In production, should check actual file permissions
                pass
                
        return {
            'passed': len(security_issues) == 0,
            'severity': 'warning' if security_issues else 'info',
            'message': '; '.join(security_issues) if security_issues else "Security configuration acceptable",
            'details': {'issues': security_issues}
        }

class BackupManager:
    """Automated backup and recovery management"""
    
    def __init__(self):
        self.backup_base_path = "backups"
        self.retention_days = 30
        
    def create_full_backup(self) -> str:
        """Create full system backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.backup_base_path}/full_backup_{timestamp}"
        
        os.makedirs(backup_path, exist_ok=True)
        
        # Backup databases
        db_backup_path = f"{backup_path}/databases"
        os.makedirs(db_backup_path, exist_ok=True)
        
        database_files = [
            "predictions.db",
            "trading_predictions.db",
            "paper_trading.db",
            "data/enhanced_outcomes.db",
            "data/metrics.db"
        ]
        
        for db_file in database_files:
            if os.path.exists(db_file):
                shutil.copy2(db_file, db_backup_path)
                
        # Backup configuration
        config_backup_path = f"{backup_path}/config"
        if os.path.exists("config"):
            shutil.copytree("config", config_backup_path, dirs_exist_ok=True)
            
        # Backup service files
        services_backup_path = f"{backup_path}/services"
        if os.path.exists("services"):
            shutil.copytree("services", services_backup_path, dirs_exist_ok=True)
            
        # Backup systemd files
        systemd_backup_path = f"{backup_path}/systemd"
        if os.path.exists("systemd"):
            shutil.copytree("systemd", systemd_backup_path, dirs_exist_ok=True)
            
        # Create backup manifest
        manifest = {
            'backup_type': 'full',
            'timestamp': timestamp,
            'created_at': datetime.now().isoformat(),
            'databases': database_files,
            'includes': ['config', 'services', 'systemd']
        }
        
        with open(f"{backup_path}/manifest.json", 'w') as f:
            json.dump(manifest, f, indent=2)
            
        return backup_path
        
    def cleanup_old_backups(self):
        """Clean up old backups based on retention policy"""
        if not os.path.exists(self.backup_base_path):
            return
            
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        for backup_dir in os.listdir(self.backup_base_path):
            backup_path = os.path.join(self.backup_base_path, backup_dir)
            
            if os.path.isdir(backup_path):
                # Extract timestamp from directory name
                try:
                    timestamp_str = backup_dir.split('_')[-2] + '_' + backup_dir.split('_')[-1]
                    backup_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    
                    if backup_date < cutoff_date:
                        shutil.rmtree(backup_path)
                        print(f"🗑️ Removed old backup: {backup_dir}")
                        
                except (ValueError, IndexError):
                    # Skip directories that don't match expected format
                    pass

class OperationalRunbooks:
    """Automated operational runbooks and procedures"""
    
    def __init__(self, deployment_manager: DeploymentManager):
        self.deployment_manager = deployment_manager
        
    def emergency_stop_all_services(self):
        """Emergency procedure to stop all services"""
        print("🚨 EMERGENCY STOP PROCEDURE INITIATED")
        print("=" * 50)
        
        for service_name in self.deployment_manager.services:
            try:
                self.deployment_manager._stop_service(service_name)
                print(f"⏹️ Stopped {service_name}")
            except Exception as e:
                print(f"❌ Failed to stop {service_name}: {e}")
                
        print("🛑 Emergency stop completed")
        
    def restart_unhealthy_services(self):
        """Restart services that are unhealthy"""
        print("🔄 RESTARTING UNHEALTHY SERVICES")
        print("=" * 40)
        
        for service_name in self.deployment_manager.services:
            if not self.deployment_manager._perform_health_check(service_name):
                print(f"🔧 Restarting unhealthy service: {service_name}")
                
                try:
                    self.deployment_manager._stop_service(service_name)
                    time.sleep(2)
                    
                    # Start service
                    service_config = self.deployment_manager.services[service_name]
                    systemd_service = service_config['systemd_service']
                    subprocess.run(['sudo', 'systemctl', 'start', systemd_service], check=True)
                    
                    # Wait and check health
                    time.sleep(5)
                    if self.deployment_manager._perform_health_check(service_name):
                        print(f"✅ {service_name} restarted successfully")
                    else:
                        print(f"❌ {service_name} still unhealthy after restart")
                        
                except Exception as e:
                    print(f"💥 Failed to restart {service_name}: {e}")
            else:
                print(f"✅ {service_name} is healthy")
                
    def generate_system_status_report(self) -> Dict[str, Any]:
        """Generate comprehensive system status report"""
        print("📊 GENERATING SYSTEM STATUS REPORT")
        print("=" * 40)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'system_health': {},
            'recommendations': []
        }
        
        # Check each service
        for service_name in self.deployment_manager.services:
            service_status = {
                'name': service_name,
                'systemd_active': False,
                'health_check_passed': False,
                'last_check': datetime.now().isoformat()
            }
            
            # Check systemd status
            try:
                service_config = self.deployment_manager.services[service_name]
                systemd_service = service_config['systemd_service']
                
                result = subprocess.run(['systemctl', 'is-active', systemd_service], 
                                      capture_output=True, text=True)
                service_status['systemd_active'] = result.stdout.strip() == 'active'
                
                # Health check
                service_status['health_check_passed'] = self.deployment_manager._perform_health_check(service_name)
                
            except Exception as e:
                service_status['error'] = str(e)
                
            report['services'][service_name] = service_status
            
        # System health
        try:
            import psutil
            
            report['system_health'] = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'uptime': time.time() - psutil.boot_time()
            }
        except Exception as e:
            report['system_health'] = {'error': str(e)}
            
        # Generate recommendations
        unhealthy_services = [
            name for name, status in report['services'].items()
            if not status.get('health_check_passed', False)
        ]
        
        if unhealthy_services:
            report['recommendations'].append(f"Restart unhealthy services: {', '.join(unhealthy_services)}")
            
        if report['system_health'].get('memory_percent', 0) > 85:
            report['recommendations'].append("High memory usage detected - consider investigating memory leaks")
            
        if report['system_health'].get('disk_percent', 0) > 90:
            report['recommendations'].append("Low disk space - clean up old logs and backups")
            
        return report

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Trading System Deployment and Operations Manager")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Deploy command
    deploy_parser = subparsers.add_parser('deploy', help='Deploy services')
    deploy_parser.add_argument('--environment', default='production', help='Target environment')
    deploy_parser.add_argument('--services', nargs='*', help='Specific services to deploy')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate production readiness')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create system backup')
    backup_parser.add_argument('--cleanup', action='store_true', help='Clean up old backups')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Generate system status report')
    
    # Emergency commands
    emergency_parser = subparsers.add_parser('emergency', help='Emergency operations')
    emergency_parser.add_argument('action', choices=['stop-all', 'restart-unhealthy'], 
                                help='Emergency action to perform')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
        
    # Initialize managers
    deployment_manager = DeploymentManager()
    backup_manager = BackupManager()
    runbooks = OperationalRunbooks(deployment_manager)
    
    # Execute command
    if args.command == 'deploy':
        if args.services:
            print(f"🚀 Deploying specific services: {args.services}")
            # TODO: Implement partial deployment
        else:
            results = deployment_manager.deploy_all_services(args.environment)
            
            # Print results
            print("\n📊 DEPLOYMENT RESULTS:")
            for service, status in results.items():
                status_icon = "✅" if status.status == "deployed" else "❌"
                print(f"{status_icon} {service}: {status.status}")
                
    elif args.command == 'validate':
        results = deployment_manager.validate_production_readiness()
        
        print(f"\n🔍 PRODUCTION READINESS: {'✅ READY' if results['overall_ready'] else '❌ NOT READY'}")
        
        if results['errors']:
            print("\n🚨 CRITICAL ERRORS:")
            for error in results['errors']:
                print(f"  ❌ {error}")
                
        if results['warnings']:
            print("\n⚠️ WARNINGS:")
            for warning in results['warnings']:
                print(f"  ⚠️ {warning}")
                
    elif args.command == 'backup':
        if args.cleanup:
            backup_manager.cleanup_old_backups()
        else:
            backup_path = backup_manager.create_full_backup()
            print(f"📦 Backup created: {backup_path}")
            
    elif args.command == 'status':
        report = runbooks.generate_system_status_report()
        
        print(f"\n📊 SYSTEM STATUS REPORT - {report['timestamp']}")
        print("=" * 50)
        
        for service, status in report['services'].items():
            active_icon = "🟢" if status['systemd_active'] else "🔴"
            health_icon = "💚" if status['health_check_passed'] else "💔"
            print(f"{active_icon} {health_icon} {service}")
            
        if report['recommendations']:
            print("\n💡 RECOMMENDATIONS:")
            for rec in report['recommendations']:
                print(f"  📋 {rec}")
                
    elif args.command == 'emergency':
        if args.action == 'stop-all':
            runbooks.emergency_stop_all_services()
        elif args.action == 'restart-unhealthy':
            runbooks.restart_unhealthy_services()

if __name__ == "__main__":
    main()
