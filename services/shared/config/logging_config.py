"""Logging configuration for services"""

import os
import logging
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_enabled: bool = True
    console_enabled: bool = True
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    log_directory: str = "logs/services"
    
    @classmethod
    def from_env(cls) -> 'LoggingConfig':
        """Create logging configuration from environment variables"""
        return cls(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            file_enabled=os.getenv("LOG_FILE_ENABLED", "true").lower() == "true",
            console_enabled=os.getenv("LOG_CONSOLE_ENABLED", "true").lower() == "true",
            max_file_size=int(os.getenv("LOG_MAX_FILE_SIZE", str(10 * 1024 * 1024))),
            backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5")),
            log_directory=os.getenv("LOG_DIRECTORY", "logs/services")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'level': self.level,
            'format': self.format,
            'file_enabled': self.file_enabled,
            'console_enabled': self.console_enabled,
            'max_file_size': self.max_file_size,
            'backup_count': self.backup_count,
            'log_directory': self.log_directory
        }


# Global logging configuration
logging_config = LoggingConfig.from_env()


def get_logging_config() -> LoggingConfig:
    """Get logging configuration"""
    return logging_config


def setup_service_logging(service_name: str) -> logging.Logger:
    """Setup logging for a service"""
    logger = logging.getLogger(service_name)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Set level
    logger.setLevel(getattr(logging, logging_config.level))
    
    # Create formatter
    formatter = logging.Formatter(logging_config.format)
    
    # Console handler
    if logging_config.console_enabled:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if logging_config.file_enabled:
        # Create log directory
        os.makedirs(logging_config.log_directory, exist_ok=True)
        
        log_file = os.path.join(logging_config.log_directory, f"{service_name}.log")
        
        try:
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=logging_config.max_file_size,
                backupCount=logging_config.backup_count
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except ImportError:
            # Fallback to basic file handler
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the service configuration"""
    return setup_service_logging(name)
