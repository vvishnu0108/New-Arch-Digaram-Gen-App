"""
Centralized logging configuration for the diagram-agent backend.
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Logging configuration from environment
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")
LOG_FORMAT = os.getenv(
    "LOG_FORMAT", 
    "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
)
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", 10 * 1024 * 1024))  # 10MB default
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 5))


def setup_logging(app_name: str = "diagram-agent") -> logging.Logger:
    """
    Set up application-wide logging with console and file handlers.
    
    Args:
        app_name: The root logger name for the application
        
    Returns:
        The configured root logger
    """
    # Ensure logs directory exists
    log_path = Path(LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Get or create root logger
    logger = logging.getLogger(app_name)
    
    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a child logger for a specific module.
    
    Args:
        name: The module name (usually __name__)
        
    Returns:
        A logger instance for the module
    """
    return logging.getLogger(f"diagram-agent.{name}")


# Initialize the root logger on import
root_logger = setup_logging()


# Convenience function for quick setup
def configure_uvicorn_logging():
    """Configure uvicorn to use our logging format."""
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers = root_logger.handlers
    
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.handlers = root_logger.handlers
    
    uvicorn_error = logging.getLogger("uvicorn.error")
    uvicorn_error.handlers = root_logger.handlers
