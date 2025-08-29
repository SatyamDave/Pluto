"""
Pluto Logging Configuration
Centralized logging setup for all modules
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

# Version constant
PLUTO_VERSION = "1.0.0"

def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: Optional[str] = None
) -> None:
    """
    Setup logging configuration for Pluto
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        log_format: Optional custom log format
    """
    
    # Default format
    if log_format is None:
        log_format = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "[%(filename)s:%(lineno)d] - %(message)s"
        )
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    loggers = {
        "pluto": "INFO",
        "sqlalchemy": "WARNING",
        "redis": "WARNING",
        "httpx": "WARNING",
        "openai": "WARNING",
        "anthropic": "WARNING"
    }
    
    for logger_name, logger_level in loggers.items():
        logging.getLogger(logger_name).setLevel(getattr(logging, logger_level.upper()))
    
    # Log startup
    logger = logging.getLogger(__name__)
    logger.info(f"Pluto v{PLUTO_VERSION} logging initialized at {level} level")
    
    if log_file:
        logger.info(f"Log file: {log_file}")

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module
    
    Args:
        name: Module name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

def log_function_call(func_name: str, **kwargs):
    """
    Decorator helper to log function calls
    
    Args:
        func_name: Name of the function being called
        **kwargs: Function arguments to log
    """
    logger = logging.getLogger(__name__)
    args_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.debug(f"Calling {func_name}({args_str})")

def log_function_result(func_name: str, result: any, **kwargs):
    """
    Log function results
    
    Args:
        func_name: Name of the function that completed
        result: Result of the function call
        **kwargs: Additional context
    """
    logger = logging.getLogger(__name__)
    context = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.debug(f"{func_name} completed - Result: {result} | Context: {context}")

def log_error(func_name: str, error: Exception, **kwargs):
    """
    Log function errors
    
    Args:
        func_name: Name of the function that failed
        error: Exception that occurred
        **kwargs: Additional context
    """
    logger = logging.getLogger(__name__)
    context = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.error(f"{func_name} failed - Error: {error} | Context: {context}")
