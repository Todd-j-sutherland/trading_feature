#!/usr/bin/env python3
"""
Configuration Management Consistency Service
Ensures uniform settings.py usage across all microservices with proper fallback mechanisms
"""
import asyncio
import os
import sys
import json
import importlib.util
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.base_service import BaseService

class ConfigurationConsistencyService(BaseService):
    """Configuration management service ensuring consistent settings.py usage"""

    def __init__(self):
        super().__init__("config-manager")
        self.config_cache = {}
        self.fallback_configs = {}
        self.validation_errors = []
        
        # Initialize configuration validation
        self.register_handler("validate_all_configs", self.validate_all_configs)
        self.register_handler("sync_configuration", self.sync_configuration)
        self.register_handler("get_config_status", self.get_config_status)
        self.register_handler("reload_configs", self.reload_configs)
        self.register_handler("validate_config_consistency", self.validate_config_consistency)
        self.register_handler("generate_config_report", self.generate_config_report)

    async def validate_all_configs(self):
        """Validate configuration consistency across all services"""
        self.logger.info('"action": "validate_all_configs_started"')
        
        config_status = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "consistency_check": {},
            "validation_errors": [],
            "fallback_usage": {}
        }

        # Load main settings.py
        main_config = await self._load_main_settings()
        if not main_config:
            config_status["critical_error"] = "Main settings.py could not be loaded"
            return config_status

        # Validate each service's configuration usage
        services = [
            "news_scraper",
            "market_data", 
            "ml_model",
            "prediction",
            "scheduler", 
            "paper_trading",
            "database_validator",
            "performance"
        ]

        for service in services:
            service_config = await self._validate_service_config(service, main_config)
            config_status["services"][service] = service_config

        # Check configuration consistency
        consistency_results = await self._check_config_consistency(config_status["services"])
        config_status["consistency_check"] = consistency_results

        # Generate fallback recommendations
        fallback_recommendations = await self._generate_fallback_configs()
        config_status["fallback_recommendations"] = fallback_recommendations

        self.logger.info(f'"action": "validate_all_configs_completed", "services_checked": {len(services)}, "errors": {len(config_status["validation_errors"])}"')
        
        return config_status

    async def _load_main_settings(self) -> Optional[Dict[str, Any]]:
        """Load and validate main settings.py configuration"""
        try:
            # Try multiple potential settings.py locations
            settings_paths = [
                "settings.py",
                "app/config/settings.py", 
                "config/settings.py",
                "../settings.py"
            ]

            for settings_path in settings_paths:
                if os.path.exists(settings_path):
                    spec = importlib.util.spec_from_file_location("settings", settings_path)
                    settings_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(settings_module)
                    
                    # Extract all configuration variables
                    config = {}
                    for attr in dir(settings_module):
                        if not attr.startswith('_'):
                            config[attr] = getattr(settings_module, attr)
                    
                    self.config_cache["main"] = config
                    self.logger.info(f'"action": "main_settings_loaded", "path": "{settings_path}", "config_keys": {len(config)}"')
                    return config

            self.logger.error('"action": "main_settings_load_failed", "error": "settings.py not found in any expected location"')
            return None

        except Exception as e:
            self.logger.error(f'"action": "main_settings_load_error", "error": "{e}"')
            return None

    async def _validate_service_config(self, service_name: str, main_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate individual service configuration usage"""
        validation_result = {
            "service": service_name,
            "config_loaded": False,
            "settings_integration": False,
            "required_configs": {},
            "missing_configs": [],
            "fallback_usage": [],
            "validation_errors": []
        }

        try:
            # Check if service has proper settings.py integration
            service_file_paths = [
                f"services/{service_name}_service.py",
                f"services/{service_name.replace('_', '-')}_service.py",
                f"services/core/{service_name}.py",
                f"services/{service_name}.py"
            ]

            service_file = None
            for path in service_file_paths:
                if os.path.exists(path):
                    service_file = path
                    break

            if not service_file:
                validation_result["validation_errors"].append(f"Service file not found for {service_name}")
                return validation_result

            # Read service file and check for settings usage
            with open(service_file, 'r', encoding='utf-8') as f:
                service_content = f.read()

            # Check for settings.py import patterns
            settings_import_patterns = [
                "from settings import",
                "import settings",
                "from config import settings",
                "from app.config.settings import"
            ]

            has_settings_import = any(pattern in service_content for pattern in settings_import_patterns)
            validation_result["settings_integration"] = has_settings_import

            if not has_settings_import:
                validation_result["validation_errors"].append("No settings.py import found")

            # Check for specific configuration usage based on service type
            required_configs = self._get_service_required_configs(service_name)
            validation_result["required_configs"] = required_configs

            for config_key in required_configs:
                if config_key not in service_content:
                    validation_result["missing_configs"].append(config_key)

            validation_result["config_loaded"] = True

        except Exception as e:
            validation_result["validation_errors"].append(f"Service validation error: {e}")

        return validation_result

    def _get_service_required_configs(self, service_name: str) -> List[str]:
        """Get required configuration keys for each service"""
        service_configs = {
            "news_scraper": [
                "NEWS_SOURCES",
                "NEWS_CONFIG", 
                "SENTIMENT_KEYWORDS",
                "RSS_CONFIG"
            ],
            "market_data": [
                "SYMBOLS",
                "ALPHA_VANTAGE_API_KEY",
                "MARKET_CONFIG",
                "TECHNICAL_INDICATORS"
            ],
            "ml_model": [
                "ML_CONFIG",
                "MODEL_PATHS",
                "TRAINING_CONFIG"
            ],
            "prediction": [
                "SYMBOLS",
                "PREDICTION_CONFIG",
                "BUY_THRESHOLDS",
                "MARKET_HOURS"
            ],
            "scheduler": [
                "SCHEDULE_CONFIG",
                "MARKET_HOURS",
                "CRON_JOBS"
            ],
            "paper_trading": [
                "PAPER_TRADING_CONFIG",
                "IG_MARKETS_CONFIG",
                "TRADING_LIMITS"
            ],
            "database_validator": [
                "DATABASE_CONFIG",
                "DB_VALIDATION_RULES"
            ],
            "performance": [
                "PERFORMANCE_CONFIG",
                "MONITORING_CONFIG",
                "SLA_REQUIREMENTS"
            ]
        }
        
        return service_configs.get(service_name, [])

    async def _check_config_consistency(self, service_configs: Dict[str, Any]) -> Dict[str, Any]:
        """Check consistency across service configurations"""
        consistency_check = {
            "timestamp": datetime.now().isoformat(),
            "inconsistencies": [],
            "warnings": [],
            "recommendations": []
        }

        # Check for common configuration inconsistencies
        services_with_settings = [
            service for service, config in service_configs.items() 
            if config.get("settings_integration", False)
        ]

        services_without_settings = [
            service for service, config in service_configs.items() 
            if not config.get("settings_integration", False)
        ]

        if services_without_settings:
            consistency_check["inconsistencies"].append({
                "type": "missing_settings_integration",
                "services": services_without_settings,
                "impact": "high",
                "description": "Services without proper settings.py integration"
            })

        # Check for missing required configurations
        for service, config in service_configs.items():
            if config.get("missing_configs"):
                consistency_check["inconsistencies"].append({
                    "type": "missing_required_configs",
                    "service": service,
                    "missing": config["missing_configs"],
                    "impact": "medium",
                    "description": f"Service {service} missing required configurations"
                })

        # Generate recommendations
        if consistency_check["inconsistencies"]:
            consistency_check["recommendations"].extend([
                "Implement uniform settings.py import pattern across all services",
                "Add fallback configuration mechanisms for missing settings",
                "Create configuration validation in service initialization",
                "Implement configuration hot-reload capability"
            ])

        return consistency_check

    async def _generate_fallback_configs(self) -> Dict[str, Any]:
        """Generate fallback configuration recommendations"""
        fallback_configs = {
            "NEWS_SOURCES": {
                "fallback": ["https://www.abc.net.au/news/feed/51120/rss.xml"],
                "type": "list",
                "critical": True
            },
            "SYMBOLS": {
                "fallback": ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX"],
                "type": "list", 
                "critical": True
            },
            "ALPHA_VANTAGE_API_KEY": {
                "fallback": "DEMO_KEY",
                "type": "string",
                "critical": False,
                "warning": "Demo key has limited functionality"
            },
            "MARKET_HOURS": {
                "fallback": {
                    "open": "10:00",
                    "close": "16:00", 
                    "timezone": "Australia/Sydney"
                },
                "type": "dict",
                "critical": True
            },
            "BUY_THRESHOLDS": {
                "fallback": {
                    "conservative": 0.75,
                    "moderate": 0.70,
                    "aggressive": 0.65
                },
                "type": "dict",
                "critical": True
            }
        }

        return fallback_configs

    async def sync_configuration(self, target_service: str = None):
        """Synchronize configuration across services"""
        if target_service:
            services = [target_service]
        else:
            services = ["news_scraper", "market_data", "ml_model", "prediction", "scheduler", "paper_trading"]

        sync_results = {
            "timestamp": datetime.now().isoformat(),
            "services_synced": [],
            "sync_errors": [],
            "configurations_updated": []
        }

        main_config = await self._load_main_settings()
        if not main_config:
            sync_results["sync_errors"].append("Cannot sync without main settings.py")
            return sync_results

        for service in services:
            try:
                # Call service to reload configuration
                reload_result = await self.call_service(service, "reload_config", timeout=10.0)
                sync_results["services_synced"].append(service)
                sync_results["configurations_updated"].append({
                    "service": service,
                    "reload_result": reload_result
                })

            except Exception as e:
                sync_results["sync_errors"].append({
                    "service": service,
                    "error": str(e)
                })

        self.logger.info(f'"action": "configuration_sync_completed", "synced": {len(sync_results["services_synced"])}, "errors": {len(sync_results["sync_errors"])}"')
        
        return sync_results

    async def get_config_status(self):
        """Get current configuration status summary"""
        return {
            "timestamp": datetime.now().isoformat(),
            "cached_configs": list(self.config_cache.keys()),
            "validation_errors": len(self.validation_errors),
            "fallback_configs_available": len(self.fallback_configs),
            "last_validation": getattr(self, 'last_validation_time', None)
        }

    async def reload_configs(self):
        """Reload all configurations from disk"""
        self.config_cache.clear()
        self.validation_errors.clear()
        
        main_config = await self._load_main_settings()
        reload_result = {
            "timestamp": datetime.now().isoformat(),
            "main_config_loaded": main_config is not None,
            "config_keys": len(main_config) if main_config else 0
        }

        self.logger.info(f'"action": "configs_reloaded", "main_config_loaded": {reload_result["main_config_loaded"]}"')
        
        return reload_result

    async def validate_config_consistency(self):
        """Quick consistency validation check"""
        validation_result = await self.validate_all_configs()
        
        consistency_score = 100
        if validation_result.get("validation_errors"):
            consistency_score -= len(validation_result["validation_errors"]) * 10
        
        inconsistencies = validation_result.get("consistency_check", {}).get("inconsistencies", [])
        if inconsistencies:
            consistency_score -= len(inconsistencies) * 15

        return {
            "consistency_score": max(0, consistency_score),
            "status": "healthy" if consistency_score >= 80 else "warning" if consistency_score >= 60 else "critical",
            "total_errors": len(validation_result.get("validation_errors", [])),
            "total_inconsistencies": len(inconsistencies)
        }

    async def generate_config_report(self):
        """Generate comprehensive configuration report"""
        validation_result = await self.validate_all_configs()
        consistency_check = await self.validate_config_consistency()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "consistency_score": consistency_check["consistency_score"],
                "status": consistency_check["status"],
                "services_checked": len(validation_result.get("services", {})),
                "total_errors": consistency_check["total_errors"],
                "total_inconsistencies": consistency_check["total_inconsistencies"]
            },
            "detailed_validation": validation_result,
            "recommendations": []
        }

        # Generate specific recommendations
        if consistency_check["consistency_score"] < 80:
            report["recommendations"].extend([
                "Review services without settings.py integration",
                "Implement missing required configurations", 
                "Add configuration validation to service startup",
                "Consider implementing configuration hot-reload"
            ])

        if validation_result.get("consistency_check", {}).get("inconsistencies"):
            report["recommendations"].append("Address configuration inconsistencies identified")

        # Save report to file
        report_file = f"config_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            report["report_saved"] = report_file
        except Exception as e:
            report["report_save_error"] = str(e)

        return report

    async def health_check(self):
        """Enhanced health check with configuration status"""
        base_health = await super().health_check()
        
        config_health = {
            **base_health,
            "main_config_loaded": "main" in self.config_cache,
            "cached_configs": len(self.config_cache),
            "validation_errors": len(self.validation_errors),
            "fallback_configs": len(self.fallback_configs)
        }

        return config_health

async def main():
    service = ConfigurationConsistencyService()
    await service.start_server()

if __name__ == "__main__":
    asyncio.run(main())
