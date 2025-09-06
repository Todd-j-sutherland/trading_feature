"""Service configuration management with environment support"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ServiceConfig:
    """Configuration for individual services"""
    name: str
    host: str = "localhost"
    port: int = 8000
    debug: bool = False
    workers: int = 1
    
    # Service-specific settings
    timeout: int = 30
    max_connections: int = 100
    enable_cors: bool = True
    
    # Authentication (future use)
    api_key: Optional[str] = None
    auth_enabled: bool = False
    
    # Feature flags
    enable_caching: bool = True
    cache_ttl: int = 300  # 5 minutes
    
    @classmethod
    def from_env(cls, service_name: str) -> 'ServiceConfig':
        """Create configuration from environment variables"""
        env_prefix = f"{service_name.upper()}_"
        
        return cls(
            name=service_name,
            host=os.getenv(f"{env_prefix}HOST", "localhost"),
            port=int(os.getenv(f"{env_prefix}PORT", "8000")),
            debug=os.getenv(f"{env_prefix}DEBUG", "false").lower() == "true",
            workers=int(os.getenv(f"{env_prefix}WORKERS", "1")),
            timeout=int(os.getenv(f"{env_prefix}TIMEOUT", "30")),
            max_connections=int(os.getenv(f"{env_prefix}MAX_CONNECTIONS", "100")),
            enable_cors=os.getenv(f"{env_prefix}ENABLE_CORS", "true").lower() == "true",
            api_key=os.getenv(f"{env_prefix}API_KEY"),
            auth_enabled=os.getenv(f"{env_prefix}AUTH_ENABLED", "false").lower() == "true",
            enable_caching=os.getenv(f"{env_prefix}ENABLE_CACHING", "true").lower() == "true",
            cache_ttl=int(os.getenv(f"{env_prefix}CACHE_TTL", "300"))
        )


# Predefined service configurations
ORCHESTRATOR_CONFIG = ServiceConfig(
    name="orchestrator",
    host="localhost",
    port=8000,
    debug=False,
    workers=2
)

TRADING_CONFIG = ServiceConfig(
    name="trading",
    host="localhost", 
    port=8001,
    debug=False,
    workers=1
)

SENTIMENT_CONFIG = ServiceConfig(
    name="sentiment",
    host="localhost",
    port=8002,
    debug=False,
    workers=1
)

ML_CONFIG = ServiceConfig(
    name="ml",
    host="localhost",
    port=8003,
    debug=False,
    workers=1
)

DATA_CONFIG = ServiceConfig(
    name="data",
    host="localhost",
    port=8004,
    debug=False,
    workers=1
)

DASHBOARD_CONFIG = ServiceConfig(
    name="dashboard",
    host="localhost",
    port=8005,
    debug=False,
    workers=1
)


class ConfigManager:
    """Central configuration manager"""
    
    def __init__(self):
        self.configs = {
            "orchestrator": ORCHESTRATOR_CONFIG,
            "trading": TRADING_CONFIG,
            "sentiment": SENTIMENT_CONFIG,
            "ml": ML_CONFIG,
            "data": DATA_CONFIG,
            "dashboard": DASHBOARD_CONFIG
        }
        
        # Override with environment variables if available
        self._load_env_configs()
    
    def _load_env_configs(self):
        """Load configurations from environment variables"""
        for service_name in self.configs.keys():
            env_config = ServiceConfig.from_env(service_name)
            # Only override if environment variables are actually set
            env_prefix = f"{service_name.upper()}_"
            if any(key.startswith(env_prefix) for key in os.environ.keys()):
                self.configs[service_name] = env_config
    
    def get_config(self, service_name: str) -> ServiceConfig:
        """Get configuration for a service"""
        config = self.configs.get(service_name)
        if not config:
            raise ValueError(f"Unknown service: {service_name}")
        return config
    
    def get_service_url(self, service_name: str) -> str:
        """Get full URL for a service"""
        config = self.get_config(service_name)
        return f"http://{config.host}:{config.port}"
    
    def get_all_services(self) -> Dict[str, str]:
        """Get all service URLs"""
        return {name: self.get_service_url(name) for name in self.configs.keys()}
    
    def register_service(self, config: ServiceConfig):
        """Register a new service configuration"""
        self.configs[config.name] = config
    
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return os.getenv("ENVIRONMENT", "development") == "development"
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return os.getenv("ENVIRONMENT", "development") == "production"


# Global configuration manager
config_manager = ConfigManager()


def get_service_config(service_name: str) -> ServiceConfig:
    """Get service configuration"""
    return config_manager.get_config(service_name)


def get_service_url(service_name: str) -> str:
    """Get service URL"""
    return config_manager.get_service_url(service_name)


def get_all_service_urls() -> Dict[str, str]:
    """Get all service URLs"""
    return config_manager.get_all_services()


# Environment helpers
def is_development() -> bool:
    """Check if running in development environment"""
    return config_manager.is_development()


def is_production() -> bool:
    """Check if running in production environment"""
    return config_manager.is_production()


def get_env_var(key: str, default: Any = None, required: bool = False) -> Any:
    """Get environment variable with validation"""
    value = os.getenv(key, default)
    
    if required and value is None:
        raise ValueError(f"Required environment variable not set: {key}")
    
    return value


def load_env_file(file_path: str = ".env"):
    """Load environment variables from file"""
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()


# Load .env file if it exists
load_env_file()
