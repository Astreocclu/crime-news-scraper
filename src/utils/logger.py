"""
Logging utility module for crime-news-scraper.

This module provides standardized logging configuration for all components
of the application, ensuring consistent log formatting, rotation, and levels
across different modules.

Usage:
    from src.utils.logger import get_logger

    # Get a logger for your module
    logger = get_logger(__name__)

    # Use the logger
    logger.info("Processing started")
    try:
        # Some code
        pass
    except Exception as e:
        logger.exception("An error occurred: %s", str(e))
"""

import logging
import logging.handlers
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Union

# Default log levels for different environments
LOG_LEVELS = {
    "development": logging.DEBUG,
    "production": logging.INFO,
}

# Log format configuration
CONSOLE_LOG_FORMAT = "%(asctime)s - %(levelname)-8s - %(name)s - %(message)s"
FILE_LOG_FORMAT = "%(asctime)s - %(levelname)-8s - %(name)s:%(lineno)d - %(funcName)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log file configuration
DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_FILE = "crime_news_scraper.log"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

# Create a dictionary to store module specific loggers
LOGGERS: Dict[str, logging.Logger] = {}

def get_log_dir() -> Path:
    """
    Get the log directory path, creating it if it doesn't exist.
    
    Returns:
        Path: The path to the log directory
    """
    # Find the project root (where we'll create the logs directory)
    # First try to find it via the repository root
    current_dir = Path(__file__).resolve().parent
    root_dir = current_dir
    
    # Navigate up until we find the project root (has src directory)
    while root_dir.name != "crime-news-scraper" and root_dir != root_dir.parent:
        root_dir = root_dir.parent
    
    # If we couldn't find it via repository name, use the parent of src
    if root_dir.name != "crime-news-scraper":
        root_dir = current_dir.parent.parent
    
    log_dir = root_dir / DEFAULT_LOG_DIR
    log_dir.mkdir(exist_ok=True)
    return log_dir

def configure_handlers(logger: logging.Logger, module_name: str) -> None:
    """
    Configure handlers for the logger including console and file handlers.
    
    Args:
        logger: The logger to configure
        module_name: The name of the module
    """
    # Clear any existing handlers
    logger.handlers = []
    
    # Configure console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(CONSOLE_LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(console_handler)
    
    # Configure file handler for general logs
    log_file = get_log_dir() / DEFAULT_LOG_FILE
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, 
        maxBytes=MAX_LOG_SIZE, 
        backupCount=LOG_BACKUP_COUNT
    )
    file_handler.setFormatter(logging.Formatter(FILE_LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(file_handler)
    
    # Configure component-specific log file if it's a main component
    components = ["scrapers", "analyzer", "nearby_finder"]
    for component in components:
        if component in module_name:
            component_log_file = get_log_dir() / f"{component}.log"
            component_handler = logging.handlers.RotatingFileHandler(
                component_log_file, 
                maxBytes=MAX_LOG_SIZE, 
                backupCount=LOG_BACKUP_COUNT
            )
            component_handler.setFormatter(logging.Formatter(FILE_LOG_FORMAT, DATE_FORMAT))
            logger.addHandler(component_handler)
            break

def get_logger(
    module_name: str, 
    level: Optional[Union[int, str]] = None,
    env: str = "development"
) -> logging.Logger:
    """
    Get a logger configured for a specific module.
    
    Args:
        module_name: The name of the module (__name__)
        level: Optional log level to override the default
        env: Environment ('development' or 'production')
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Return existing logger if already configured
    if module_name in LOGGERS:
        return LOGGERS[module_name]
    
    # Create new logger
    logger = logging.getLogger(module_name)
    
    # Set log level based on environment or override
    if level is not None:
        logger.setLevel(level)
    else:
        default_level = LOG_LEVELS.get(env, logging.INFO)
        logger.setLevel(default_level)
    
    # Configure handlers
    configure_handlers(logger, module_name)
    
    # Store in module dictionary
    LOGGERS[module_name] = logger
    
    return logger

def log_execution_time(logger: logging.Logger, prefix: str = ""):
    """
    Decorator to log function execution time.
    
    Args:
        logger: The logger to use
        prefix: Optional prefix for the log message
    
    Returns:
        Decorated function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            function_name = func.__name__
            logger.debug(f"{prefix}Starting {function_name}")
            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                elapsed_time = end_time - start_time
                logger.debug(f"{prefix}{function_name} completed in {elapsed_time:.2f} seconds")
                return result
            except Exception as e:
                end_time = time.time()
                elapsed_time = end_time - start_time
                logger.exception(
                    f"{prefix}{function_name} failed after {elapsed_time:.2f} seconds: {str(e)}"
                )
                raise
        return wrapper
    return decorator

def get_dated_log_filename(base_name: str, extension: str = "log") -> str:
    """
    Generate a timestamped log filename.
    
    Args:
        base_name: The base name for the log file
        extension: The file extension (default: log)
    
    Returns:
        str: Filename with timestamp
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}.{extension}"