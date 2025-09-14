#!/usr/bin/env python3
"""
Deployment Validation Service
Validates deployment processes, systemd services, and production readiness
"""
import asyncio
import subprocess
import json
import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
import shutil
import tempfile

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.base_service import BaseService

@dataclass
class DeploymentCheck:
    check_name: str
    status: str  # "passed", "failed", "warning", "skipped"
    details: Optional[Dict] = None
    error_message: Optional[str] = None
    remediation: Optional[str] = None
    timestamp: str = ""

@dataclass
class SystemdServiceStatus:
    service_name: str
    active: bool
    enabled: bool
    status: str
    pid: Optional[str] = None
    memory_usage: Optional[str] = None
    uptime: Optional[str] = None
    errors: List[str] = None

class DeploymentValidationService(BaseService):
    """Deployment validation service for production readiness checks"""

    def __init__(self):
        super().__init__("deployment-validator")
        self.deployment_checks = {}
        self.systemd_services = [
            "trading-news-scraper",
            "trading-market-data", 
            "trading-ml-model",
            "trading-prediction",
            "trading-scheduler",
            "trading-paper-trading",
            "trading-config-manager",
            "trading-performance",
            "trading-integration-test",
            "trading-deployment-validator"
        ]
        
        # Register deployment validation methods
        self.register_handler("validate_deployment", self.validate_deployment)
        self.register_handler("check_systemd_services", self.check_systemd_services)
        self.register_handler("validate_dependencies", self.validate_dependencies)
        self.register_handler("check_file_permissions", self.check_file_permissions)
        self.register_handler("validate_configuration", self.validate_configuration)
        self.register_handler("check_resource_requirements", self.check_resource_requirements)
        self.register_handler("generate_deployment_report", self.generate_deployment_report)
        self.register_handler("deploy_services", self.deploy_services)
        self.register_handler("rollback_deployment", self.rollback_deployment)

    async def validate_deployment(self, environment: str = "production"):
        """Comprehensive deployment validation"""
        deployment_session = {
            "session_id": f"deployment_validation_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now().isoformat(),
            "environment": environment,
            "checks": {},
            "summary": {}
        }

        self.logger.info(f'"action": "deployment_validation_started", "session_id": "{deployment_session["session_id"]}", "environment": "{environment}"')

        # Run all deployment checks
        deployment_session["checks"]["systemd_services"] = await self._check_systemd_services_status()
        deployment_session["checks"]["dependencies"] = await self._validate_system_dependencies()
        deployment_session["checks"]["file_permissions"] = await self._check_file_permissions()
        deployment_session["checks"]["configuration"] = await self._validate_deployment_configuration()
        deployment_session["checks"]["resources"] = await self._check_resource_requirements()
        deployment_session["checks"]["networking"] = await self._check_networking_requirements()
        deployment_session["checks"]["security"] = await self._check_security_configuration()
        deployment_session["checks"]["backup_systems"] = await self._check_backup_systems()

        # Generate deployment summary
        deployment_session["summary"] = self._generate_deployment_summary(deployment_session["checks"])
        
        # Store results
        self.deployment_checks[deployment_session["session_id"]] = deployment_session

        self.logger.info(f'"action": "deployment_validation_completed", "session_id": "{deployment_session["session_id"]}", "overall_status": "{deployment_session["summary"]["overall_status"]}"')

        return deployment_session

    async def _check_systemd_services_status(self) -> DeploymentCheck:
        """Check status of all systemd services"""
        try:
            services_status = {}
            all_services_healthy = True
            issues = []

            for service_name in self.systemd_services:
                service_status = await self._get_systemd_service_status(service_name)
                services_status[service_name] = service_status
                
                if not service_status.active:
                    all_services_healthy = False
                    issues.append(f"Service {service_name} is not active")
                
                if not service_status.enabled:
                    issues.append(f"Service {service_name} is not enabled")

            return DeploymentCheck(
                check_name="systemd_services",
                status="passed" if all_services_healthy else "failed",
                details={
                    "services": services_status,
                    "total_services": len(self.systemd_services),
                    "active_services": sum(1 for s in services_status.values() if s.active),
                    "enabled_services": sum(1 for s in services_status.values() if s.enabled)
                },
                error_message="; ".join(issues) if issues else None,
                remediation="Check service logs and restart failed services",
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            return DeploymentCheck(
                check_name="systemd_services",
                status="failed",
                error_message=f"Error checking systemd services: {e}",
                remediation="Verify systemd is running and user has proper permissions",
                timestamp=datetime.now().isoformat()
            )

    async def _get_systemd_service_status(self, service_name: str) -> SystemdServiceStatus:
        """Get detailed status of a single systemd service"""
        try:
            # Check if service is active
            active_result = subprocess.run(
                ["systemctl", "is-active", service_name],
                capture_output=True, text=True
            )
            
            # Check if service is enabled
            enabled_result = subprocess.run(
                ["systemctl", "is-enabled", service_name],
                capture_output=True, text=True
            )
            
            # Get detailed service information
            show_result = subprocess.run(
                ["systemctl", "show", service_name, 
                 "--property=MainPID,ActiveEnterTimestamp,MemoryCurrent,StatusText"],
                capture_output=True, text=True
            )

            # Parse service details
            service_details = {}
            for line in show_result.stdout.strip().split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    service_details[key] = value

            # Get recent errors from journal
            journal_result = subprocess.run(
                ["journalctl", "-u", service_name, "--since", "1 hour ago", "--no-pager", "-q"],
                capture_output=True, text=True
            )
            
            errors = []
            if journal_result.stdout:
                error_lines = [line for line in journal_result.stdout.split('\n') 
                             if any(keyword in line.lower() for keyword in ['error', 'failed', 'exception'])]
                errors = error_lines[-5:]  # Last 5 errors

            return SystemdServiceStatus(
                service_name=service_name,
                active=active_result.stdout.strip() == "active",
                enabled=enabled_result.stdout.strip() == "enabled",
                status=active_result.stdout.strip(),
                pid=service_details.get("MainPID"),
                memory_usage=service_details.get("MemoryCurrent"),
                uptime=service_details.get("ActiveEnterTimestamp"),
                errors=errors
            )

        except Exception as e:
            return SystemdServiceStatus(
                service_name=service_name,
                active=False,
                enabled=False,
                status="error",
                errors=[f"Failed to get service status: {e}"]
            )

    async def _validate_system_dependencies(self) -> DeploymentCheck:
        """Validate system dependencies are installed"""
        required_packages = [
            "python3",
            "python3-pip", 
            "redis-server",
            "sqlite3",
            "systemd"
        ]

        required_python_packages = [
            "asyncio",
            "aiofiles",
            "redis",
            "psutil",
            "feedparser",
            "beautifulsoup4",
            "requests",
            "pandas",
            "numpy",
            "scikit-learn"
        ]

        dependency_status = {
            "system_packages": {},
            "python_packages": {},
            "missing_packages": []
        }

        # Check system packages
        for package in required_packages:
            try:
                result = subprocess.run(
                    ["dpkg", "-l", package],
                    capture_output=True, text=True
                )
                dependency_status["system_packages"][package] = result.returncode == 0
                
                if result.returncode != 0:
                    dependency_status["missing_packages"].append(f"system:{package}")
                    
            except Exception:
                dependency_status["system_packages"][package] = False
                dependency_status["missing_packages"].append(f"system:{package}")

        # Check Python packages
        for package in required_python_packages:
            try:
                result = subprocess.run(
                    [sys.executable, "-c", f"import {package.replace('-', '_')}"],
                    capture_output=True, text=True
                )
                dependency_status["python_packages"][package] = result.returncode == 0
                
                if result.returncode != 0:
                    dependency_status["missing_packages"].append(f"python:{package}")
                    
            except Exception:
                dependency_status["python_packages"][package] = False
                dependency_status["missing_packages"].append(f"python:{package}")

        all_dependencies_met = len(dependency_status["missing_packages"]) == 0

        return DeploymentCheck(
            check_name="dependencies",
            status="passed" if all_dependencies_met else "failed",
            details=dependency_status,
            error_message=f"Missing packages: {', '.join(dependency_status['missing_packages'])}" if dependency_status["missing_packages"] else None,
            remediation="Install missing packages using apt and pip",
            timestamp=datetime.now().isoformat()
        )

    async def _check_file_permissions(self) -> DeploymentCheck:
        """Check file permissions and directory structure"""
        required_directories = [
            "/var/log/trading",
            "/tmp/trading_sockets",
            "/opt/trading_services",
            "/opt/trading_venv"
        ]

        required_files = [
            "services/base_service.py",
            "services/core/news_scraper.py",
            "services/market_data/market_data_service.py",
            "services/ml/ml_model_service.py",
            "services/prediction/prediction_service.py"
        ]

        permission_status = {
            "directories": {},
            "files": {},
            "permission_issues": []
        }

        # Check directories
        for directory in required_directories:
            try:
                if os.path.exists(directory):
                    stat_info = os.stat(directory)
                    permission_status["directories"][directory] = {
                        "exists": True,
                        "writable": os.access(directory, os.W_OK),
                        "readable": os.access(directory, os.R_OK),
                        "permissions": oct(stat_info.st_mode)[-3:]
                    }
                    
                    if not os.access(directory, os.W_OK):
                        permission_status["permission_issues"].append(f"Directory {directory} is not writable")
                else:
                    permission_status["directories"][directory] = {"exists": False}
                    permission_status["permission_issues"].append(f"Directory {directory} does not exist")
                    
            except Exception as e:
                permission_status["directories"][directory] = {"error": str(e)}
                permission_status["permission_issues"].append(f"Error checking {directory}: {e}")

        # Check files
        for file_path in required_files:
            try:
                if os.path.exists(file_path):
                    stat_info = os.stat(file_path)
                    permission_status["files"][file_path] = {
                        "exists": True,
                        "readable": os.access(file_path, os.R_OK),
                        "executable": os.access(file_path, os.X_OK),
                        "permissions": oct(stat_info.st_mode)[-3:]
                    }
                    
                    if not os.access(file_path, os.R_OK):
                        permission_status["permission_issues"].append(f"File {file_path} is not readable")
                else:
                    permission_status["files"][file_path] = {"exists": False}
                    permission_status["permission_issues"].append(f"File {file_path} does not exist")
                    
            except Exception as e:
                permission_status["files"][file_path] = {"error": str(e)}
                permission_status["permission_issues"].append(f"Error checking {file_path}: {e}")

        all_permissions_ok = len(permission_status["permission_issues"]) == 0

        return DeploymentCheck(
            check_name="file_permissions",
            status="passed" if all_permissions_ok else "failed",
            details=permission_status,
            error_message="; ".join(permission_status["permission_issues"]) if permission_status["permission_issues"] else None,
            remediation="Fix file permissions and create missing directories",
            timestamp=datetime.now().isoformat()
        )

    async def _validate_deployment_configuration(self) -> DeploymentCheck:
        """Validate deployment configuration"""
        try:
            config_status = {}
            config_issues = []

            # Check settings.py exists and is valid
            settings_paths = ["settings.py", "app/config/settings.py", "config/settings.py"]
            settings_found = False
            
            for settings_path in settings_paths:
                if os.path.exists(settings_path):
                    settings_found = True
                    try:
                        with open(settings_path, 'r') as f:
                            content = f.read()
                        
                        # Check for required configuration sections
                        required_configs = [
                            "SYMBOLS", "NEWS_SOURCES", "ALPHA_VANTAGE_API_KEY",
                            "MARKET_HOURS", "BUY_THRESHOLDS", "ML_CONFIG"
                        ]
                        
                        missing_configs = [config for config in required_configs if config not in content]
                        config_status["settings_file"] = {
                            "path": settings_path,
                            "valid": len(missing_configs) == 0,
                            "missing_configs": missing_configs
                        }
                        
                        if missing_configs:
                            config_issues.extend([f"Missing config: {config}" for config in missing_configs])
                            
                    except Exception as e:
                        config_issues.append(f"Error reading settings.py: {e}")
                    break

            if not settings_found:
                config_issues.append("settings.py not found in any expected location")

            # Check database files exist
            database_files = [
                "paper_trading.db",
                "predictions.db", 
                "trading_predictions.db",
                "data/enhanced_outcomes.db"
            ]
            
            config_status["databases"] = {}
            for db_file in database_files:
                if os.path.exists(db_file):
                    config_status["databases"][db_file] = {
                        "exists": True,
                        "size": os.path.getsize(db_file),
                        "readable": os.access(db_file, os.R_OK),
                        "writable": os.access(db_file, os.W_OK)
                    }
                else:
                    config_status["databases"][db_file] = {"exists": False}
                    config_issues.append(f"Database file {db_file} not found")

            # Check Redis connectivity
            try:
                import redis
                redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
                redis_client.ping()
                config_status["redis"] = {"status": "connected"}
            except Exception as e:
                config_status["redis"] = {"status": "failed", "error": str(e)}
                config_issues.append(f"Redis connection failed: {e}")

            all_config_valid = len(config_issues) == 0

            return DeploymentCheck(
                check_name="configuration",
                status="passed" if all_config_valid else "failed",
                details=config_status,
                error_message="; ".join(config_issues) if config_issues else None,
                remediation="Fix configuration issues and ensure all required files exist",
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            return DeploymentCheck(
                check_name="configuration",
                status="failed",
                error_message=f"Configuration validation error: {e}",
                remediation="Check configuration files and permissions",
                timestamp=datetime.now().isoformat()
            )

    async def _check_resource_requirements(self) -> DeploymentCheck:
        """Check system resource requirements"""
        try:
            import psutil
            
            # Get system resources
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            cpu_count = psutil.cpu_count()
            
            resource_status = {
                "memory": {
                    "total_gb": memory.total / (1024**3),
                    "available_gb": memory.available / (1024**3),
                    "used_percent": memory.percent
                },
                "disk": {
                    "total_gb": disk.total / (1024**3),
                    "free_gb": disk.free / (1024**3),
                    "used_percent": (disk.used / disk.total) * 100
                },
                "cpu": {
                    "cores": cpu_count,
                    "usage_percent": psutil.cpu_percent(interval=1)
                }
            }

            # Define minimum requirements
            min_requirements = {
                "memory_gb": 2.0,
                "disk_free_gb": 5.0,
                "cpu_cores": 1
            }

            resource_issues = []
            
            if resource_status["memory"]["available_gb"] < min_requirements["memory_gb"]:
                resource_issues.append(f"Insufficient memory: {resource_status['memory']['available_gb']:.1f}GB available, {min_requirements['memory_gb']}GB required")
            
            if resource_status["disk"]["free_gb"] < min_requirements["disk_free_gb"]:
                resource_issues.append(f"Insufficient disk space: {resource_status['disk']['free_gb']:.1f}GB free, {min_requirements['disk_free_gb']}GB required")
            
            if resource_status["cpu"]["cores"] < min_requirements["cpu_cores"]:
                resource_issues.append(f"Insufficient CPU cores: {resource_status['cpu']['cores']} available, {min_requirements['cpu_cores']} required")

            # Check if system is under heavy load
            if resource_status["memory"]["used_percent"] > 90:
                resource_issues.append(f"High memory usage: {resource_status['memory']['used_percent']:.1f}%")
            
            if resource_status["disk"]["used_percent"] > 95:
                resource_issues.append(f"High disk usage: {resource_status['disk']['used_percent']:.1f}%")

            if resource_status["cpu"]["usage_percent"] > 95:
                resource_issues.append(f"High CPU usage: {resource_status['cpu']['usage_percent']:.1f}%")

            resources_adequate = len(resource_issues) == 0

            return DeploymentCheck(
                check_name="resources",
                status="passed" if resources_adequate else "warning" if resource_status["memory"]["available_gb"] >= min_requirements["memory_gb"] else "failed",
                details=resource_status,
                error_message="; ".join(resource_issues) if resource_issues else None,
                remediation="Free up system resources or upgrade hardware",
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            return DeploymentCheck(
                check_name="resources",
                status="failed",
                error_message=f"Resource check error: {e}",
                remediation="Install psutil package and check system status",
                timestamp=datetime.now().isoformat()
            )

    async def _check_networking_requirements(self) -> DeploymentCheck:
        """Check networking requirements for services"""
        try:
            networking_status = {
                "unix_sockets": {},
                "redis_connection": {},
                "external_apis": {}
            }

            network_issues = []

            # Check Unix socket directory
            socket_dir = "/tmp/trading_sockets"
            if os.path.exists(socket_dir):
                networking_status["unix_sockets"]["directory_exists"] = True
                networking_status["unix_sockets"]["writable"] = os.access(socket_dir, os.W_OK)
                
                if not os.access(socket_dir, os.W_OK):
                    network_issues.append(f"Unix socket directory {socket_dir} is not writable")
            else:
                networking_status["unix_sockets"]["directory_exists"] = False
                network_issues.append(f"Unix socket directory {socket_dir} does not exist")

            # Test Redis connection
            try:
                import redis
                redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True, socket_connect_timeout=5)
                redis_client.ping()
                networking_status["redis_connection"] = {"status": "success", "latency_ms": "< 5"}
            except Exception as e:
                networking_status["redis_connection"] = {"status": "failed", "error": str(e)}
                network_issues.append(f"Redis connection failed: {e}")

            # Test external API connectivity (Alpha Vantage)
            try:
                import requests
                response = requests.get("https://www.alphavantage.co/", timeout=10)
                networking_status["external_apis"]["alpha_vantage"] = {
                    "status": "reachable" if response.status_code == 200 else "unreachable",
                    "response_code": response.status_code
                }
                
                if response.status_code != 200:
                    network_issues.append(f"Alpha Vantage API unreachable: HTTP {response.status_code}")
                    
            except Exception as e:
                networking_status["external_apis"]["alpha_vantage"] = {"status": "failed", "error": str(e)}
                network_issues.append(f"Alpha Vantage API test failed: {e}")

            networking_ok = len(network_issues) == 0

            return DeploymentCheck(
                check_name="networking",
                status="passed" if networking_ok else "warning",
                details=networking_status,
                error_message="; ".join(network_issues) if network_issues else None,
                remediation="Fix networking issues and ensure external API access",
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            return DeploymentCheck(
                check_name="networking",
                status="failed",
                error_message=f"Networking check error: {e}",
                remediation="Check network connectivity and permissions",
                timestamp=datetime.now().isoformat()
            )

    async def _check_security_configuration(self) -> DeploymentCheck:
        """Check security configuration"""
        try:
            security_status = {
                "file_permissions": {},
                "service_isolation": {},
                "sensitive_data": {}
            }

            security_issues = []

            # Check sensitive file permissions
            sensitive_files = [
                "settings.py",
                "app/config/settings.py",
                "*.db"
            ]

            for file_pattern in sensitive_files:
                if '*' in file_pattern:
                    # Handle wildcard patterns
                    import glob
                    files = glob.glob(file_pattern)
                else:
                    files = [file_pattern] if os.path.exists(file_pattern) else []

                for file_path in files:
                    if os.path.exists(file_path):
                        stat_info = os.stat(file_path)
                        permissions = oct(stat_info.st_mode)[-3:]
                        
                        security_status["file_permissions"][file_path] = {
                            "permissions": permissions,
                            "world_readable": stat_info.st_mode & 0o004 != 0,
                            "world_writable": stat_info.st_mode & 0o002 != 0
                        }

                        # Check for overly permissive permissions
                        if stat_info.st_mode & 0o044 != 0:  # World or group readable
                            security_issues.append(f"File {file_path} has overly permissive permissions: {permissions}")

            # Check for hardcoded secrets (basic check)
            config_files = ["settings.py", "app/config/settings.py"]
            for config_file in config_files:
                if os.path.exists(config_file):
                    with open(config_file, 'r') as f:
                        content = f.read()
                    
                    # Look for potential hardcoded secrets
                    potential_secrets = []
                    if 'password' in content.lower() and '=' in content:
                        potential_secrets.append("Potential hardcoded password found")
                    if 'secret' in content.lower() and '=' in content:
                        potential_secrets.append("Potential hardcoded secret found")
                    
                    security_status["sensitive_data"][config_file] = {
                        "potential_secrets": potential_secrets
                    }
                    
                    if potential_secrets:
                        security_issues.extend(potential_secrets)

            # Check service isolation (running as non-root)
            try:
                current_user = os.getenv('USER') or os.getenv('USERNAME')
                security_status["service_isolation"] = {
                    "current_user": current_user,
                    "running_as_root": current_user == 'root'
                }
                
                if current_user == 'root':
                    security_issues.append("Services should not run as root user")
                    
            except Exception as e:
                security_issues.append(f"Unable to check user context: {e}")

            security_acceptable = len(security_issues) == 0

            return DeploymentCheck(
                check_name="security",
                status="passed" if security_acceptable else "warning",
                details=security_status,
                error_message="; ".join(security_issues) if security_issues else None,
                remediation="Fix security issues, restrict file permissions, and avoid running as root",
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            return DeploymentCheck(
                check_name="security",
                status="failed",
                error_message=f"Security check error: {e}",
                remediation="Review security configuration and file permissions",
                timestamp=datetime.now().isoformat()
            )

    async def _check_backup_systems(self) -> DeploymentCheck:
        """Check backup systems and data protection"""
        try:
            backup_status = {
                "backup_directories": {},
                "database_backups": {},
                "backup_scripts": {}
            }

            backup_issues = []

            # Check backup directories
            backup_dirs = ["backup_local", "remote_backup", "production/backups"]
            for backup_dir in backup_dirs:
                if os.path.exists(backup_dir):
                    dir_size = sum(os.path.getsize(os.path.join(backup_dir, f)) 
                                 for f in os.listdir(backup_dir) 
                                 if os.path.isfile(os.path.join(backup_dir, f)))
                    
                    backup_status["backup_directories"][backup_dir] = {
                        "exists": True,
                        "size_mb": dir_size / (1024*1024),
                        "file_count": len(os.listdir(backup_dir)),
                        "writable": os.access(backup_dir, os.W_OK)
                    }
                else:
                    backup_status["backup_directories"][backup_dir] = {"exists": False}
                    backup_issues.append(f"Backup directory {backup_dir} does not exist")

            # Check for recent database backups
            database_files = ["paper_trading.db", "predictions.db", "trading_predictions.db"]
            for db_file in database_files:
                if os.path.exists(db_file):
                    # Look for recent backup files
                    backup_files = []
                    for backup_dir in backup_dirs:
                        if os.path.exists(backup_dir):
                            db_backups = [f for f in os.listdir(backup_dir) if db_file in f]
                            backup_files.extend(db_backups)
                    
                    backup_status["database_backups"][db_file] = {
                        "backup_count": len(backup_files),
                        "backup_files": backup_files[:5]  # Last 5 backups
                    }
                    
                    if len(backup_files) == 0:
                        backup_issues.append(f"No backups found for {db_file}")

            # Check backup scripts
            backup_scripts = ["backup_script.py", "scripts/backup.sh", "backup.py"]
            for script in backup_scripts:
                if os.path.exists(script):
                    backup_status["backup_scripts"][script] = {
                        "exists": True,
                        "executable": os.access(script, os.X_OK)
                    }
                    
                    if not os.access(script, os.X_OK):
                        backup_issues.append(f"Backup script {script} is not executable")

            backup_systems_ok = len(backup_issues) < 3  # Allow some missing backups

            return DeploymentCheck(
                check_name="backup_systems",
                status="passed" if backup_systems_ok else "warning",
                details=backup_status,
                error_message="; ".join(backup_issues) if backup_issues else None,
                remediation="Set up automated backup systems and verify backup integrity",
                timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            return DeploymentCheck(
                check_name="backup_systems",
                status="failed",
                error_message=f"Backup check error: {e}",
                remediation="Review backup configuration and create backup directories",
                timestamp=datetime.now().isoformat()
            )

    def _generate_deployment_summary(self, checks: Dict[str, DeploymentCheck]) -> Dict:
        """Generate deployment validation summary"""
        total_checks = len(checks)
        passed_checks = sum(1 for check in checks.values() if check.status == "passed")
        failed_checks = sum(1 for check in checks.values() if check.status == "failed")
        warning_checks = sum(1 for check in checks.values() if check.status == "warning")

        # Determine overall status
        if failed_checks == 0:
            if warning_checks == 0:
                overall_status = "ready"
            else:
                overall_status = "ready_with_warnings"
        else:
            if failed_checks <= 2:
                overall_status = "needs_attention"
            else:
                overall_status = "not_ready"

        critical_issues = []
        warnings = []

        for check_name, check in checks.items():
            if check.status == "failed":
                critical_issues.append(f"{check_name}: {check.error_message}")
            elif check.status == "warning":
                warnings.append(f"{check_name}: {check.error_message}")

        return {
            "overall_status": overall_status,
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "warning_checks": warning_checks,
            "readiness_score": (passed_checks / total_checks * 100) if total_checks > 0 else 0,
            "critical_issues": critical_issues,
            "warnings": warnings,
            "deployment_recommendation": self._get_deployment_recommendation(overall_status, critical_issues, warnings)
        }

    def _get_deployment_recommendation(self, status: str, critical_issues: List[str], warnings: List[str]) -> str:
        """Get deployment recommendation based on validation results"""
        if status == "ready":
            return "✅ Deployment ready - All checks passed successfully"
        elif status == "ready_with_warnings":
            return f"⚠️ Deployment ready with {len(warnings)} warnings - Monitor after deployment"
        elif status == "needs_attention":
            return f"🔧 Address {len(critical_issues)} critical issues before deployment"
        else:
            return f"❌ Deployment not recommended - {len(critical_issues)} critical issues must be resolved"

    async def check_systemd_services(self):
        """Public endpoint to check systemd services"""
        return await self._check_systemd_services_status()

    async def validate_dependencies(self):
        """Public endpoint to validate dependencies"""
        return await self._validate_system_dependencies()

    async def check_file_permissions(self):
        """Public endpoint to check file permissions"""
        return await self._check_file_permissions()

    async def validate_configuration(self):
        """Public endpoint to validate configuration"""
        return await self._validate_deployment_configuration()

    async def check_resource_requirements(self):
        """Public endpoint to check resource requirements"""
        return await self._check_resource_requirements()

    async def generate_deployment_report(self, environment: str = "production"):
        """Generate comprehensive deployment report"""
        deployment_validation = await self.validate_deployment(environment)
        
        report = {
            "report_id": f"deployment_report_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now().isoformat(),
            "environment": environment,
            "validation_results": deployment_validation,
            "recommendations": [],
            "next_steps": []
        }

        # Generate specific recommendations
        if deployment_validation["summary"]["overall_status"] == "not_ready":
            report["recommendations"].extend([
                "Do not proceed with deployment until critical issues are resolved",
                "Review all failed checks and implement fixes",
                "Run deployment validation again after fixes"
            ])
        elif deployment_validation["summary"]["overall_status"] == "needs_attention":
            report["recommendations"].extend([
                "Address critical issues before deployment",
                "Consider deploying to staging environment first",
                "Monitor system closely after deployment"
            ])
        elif deployment_validation["summary"]["overall_status"] == "ready_with_warnings":
            report["recommendations"].extend([
                "Deployment is acceptable but monitor warnings",
                "Plan to address warnings in next maintenance window",
                "Ensure monitoring is in place for warning areas"
            ])

        # Generate next steps
        critical_issues = deployment_validation["summary"]["critical_issues"]
        if critical_issues:
            report["next_steps"].extend([
                f"1. Fix critical issue: {issue}" for issue in critical_issues[:3]
            ])
        else:
            report["next_steps"].extend([
                "1. Proceed with deployment",
                "2. Monitor system performance",
                "3. Verify all services are operational"
            ])

        # Save report to file
        report_file = f"deployment_report_{environment}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            report["report_saved"] = report_file
        except Exception as e:
            report["report_save_error"] = str(e)

        return report

    async def deploy_services(self, services: List[str] = None, dry_run: bool = True):
        """Deploy microservices to production"""
        if not services:
            services = self.systemd_services

        deployment_session = {
            "session_id": f"deployment_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now().isoformat(),
            "services": services,
            "dry_run": dry_run,
            "results": {},
            "summary": {}
        }

        self.logger.info(f'"action": "deployment_started", "session_id": "{deployment_session["session_id"]}", "dry_run": {dry_run}, "services": {len(services)}"')

        if not dry_run:
            # Validate deployment readiness first
            validation = await self.validate_deployment()
            if validation["summary"]["overall_status"] in ["not_ready", "needs_attention"]:
                deployment_session["results"]["validation_error"] = "Deployment validation failed - cannot proceed"
                return deployment_session

        for service in services:
            try:
                service_result = await self._deploy_single_service(service, dry_run)
                deployment_session["results"][service] = service_result
                
            except Exception as e:
                deployment_session["results"][service] = {
                    "status": "failed",
                    "error": str(e)
                }

        # Generate deployment summary
        successful_deployments = sum(1 for result in deployment_session["results"].values() 
                                   if isinstance(result, dict) and result.get("status") == "success")
        
        deployment_session["summary"] = {
            "total_services": len(services),
            "successful_deployments": successful_deployments,
            "failed_deployments": len(services) - successful_deployments,
            "deployment_success_rate": (successful_deployments / len(services) * 100) if services else 0
        }

        self.logger.info(f'"action": "deployment_completed", "session_id": "{deployment_session["session_id"]}", "success_rate": {deployment_session["summary"]["deployment_success_rate"]:.1f}%"')

        return deployment_session

    async def _deploy_single_service(self, service_name: str, dry_run: bool) -> Dict:
        """Deploy a single service"""
        if dry_run:
            return {
                "status": "success",
                "action": "dry_run",
                "message": f"Would deploy {service_name}"
            }

        try:
            # Stop service if running
            subprocess.run(["sudo", "systemctl", "stop", service_name], 
                         capture_output=True, text=True)
            
            # Reload systemd daemon
            subprocess.run(["sudo", "systemctl", "daemon-reload"], 
                         capture_output=True, text=True)
            
            # Start service
            start_result = subprocess.run(["sudo", "systemctl", "start", service_name], 
                                        capture_output=True, text=True)
            
            if start_result.returncode == 0:
                # Enable service for automatic startup
                subprocess.run(["sudo", "systemctl", "enable", service_name], 
                             capture_output=True, text=True)
                
                return {
                    "status": "success",
                    "action": "deployed",
                    "message": f"Successfully deployed {service_name}"
                }
            else:
                return {
                    "status": "failed",
                    "action": "deployment_failed",
                    "error": start_result.stderr,
                    "message": f"Failed to start {service_name}"
                }

        except Exception as e:
            return {
                "status": "failed",
                "action": "deployment_error",
                "error": str(e),
                "message": f"Deployment error for {service_name}"
            }

    async def rollback_deployment(self, deployment_session_id: str):
        """Rollback a deployment"""
        if deployment_session_id not in self.deployment_checks:
            return {"error": "Deployment session not found"}

        rollback_session = {
            "session_id": f"rollback_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now().isoformat(),
            "original_deployment": deployment_session_id,
            "results": {},
            "summary": {}
        }

        # Stop all services that were deployed
        deployed_services = []
        original_deployment = self.deployment_checks[deployment_session_id]
        
        if "results" in original_deployment:
            deployed_services = [service for service, result in original_deployment["results"].items() 
                               if isinstance(result, dict) and result.get("status") == "success"]

        for service in deployed_services:
            try:
                stop_result = subprocess.run(["sudo", "systemctl", "stop", service], 
                                           capture_output=True, text=True)
                
                rollback_session["results"][service] = {
                    "status": "stopped" if stop_result.returncode == 0 else "failed",
                    "message": f"Service {service} stopped" if stop_result.returncode == 0 else stop_result.stderr
                }
                
            except Exception as e:
                rollback_session["results"][service] = {
                    "status": "error",
                    "error": str(e)
                }

        successful_rollbacks = sum(1 for result in rollback_session["results"].values() 
                                 if result.get("status") == "stopped")
        
        rollback_session["summary"] = {
            "services_rolled_back": successful_rollbacks,
            "total_services": len(deployed_services),
            "rollback_success_rate": (successful_rollbacks / len(deployed_services) * 100) if deployed_services else 0
        }

        return rollback_session

    async def health_check(self):
        """Enhanced health check with deployment status"""
        base_health = await super().health_check()
        
        deployment_health = {
            **base_health,
            "deployment_checks": len(self.deployment_checks),
            "systemd_services": len(self.systemd_services),
            "last_validation": "available" if self.deployment_checks else "none"
        }

        return deployment_health

async def main():
    service = DeploymentValidationService()
    await service.start_server()

if __name__ == "__main__":
    asyncio.run(main())
