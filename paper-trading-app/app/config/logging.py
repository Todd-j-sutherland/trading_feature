"""
Centralized logging configuration for Trading Analysis System
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    max_bytes: int = 10_000_000,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Setup centralized logging configuration
    
    Args:
        level: Logging level (default: INFO)
        log_file: Optional log file path
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
    """
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('plotly').setLevel(logging.WARNING)
    
    logging.info("Logging configuration initialized")

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(name)
