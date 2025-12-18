"""
Centralized logging module for FreeTranscriber.

This module provides a singleton logger instance that outputs to both console and file.
Format: [TIMESTAMP] [LEVEL] [MODULE] Message

Usage:
    from src.core.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Application started")
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


_logger_instance: Optional[logging.Logger] = None


def get_logger(name: str = "FreeTranscriber") -> logging.Logger:
    """
    Get or create a singleton logger instance.

    Args:
        name: Logger name (typically __name__ from calling module)

    Returns:
        Configured logger instance with console and file handlers
    """
    global _logger_instance

    # Return existing logger if already initialized
    if _logger_instance is not None:
        return _logger_instance.getChild(name) if name != "FreeTranscriber" else _logger_instance

    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Create root logger
    _logger_instance = logging.getLogger("FreeTranscriber")
    _logger_instance.setLevel(logging.DEBUG)

    # Avoid adding handlers multiple times
    if _logger_instance.handlers:
        return _logger_instance.getChild(name) if name != "FreeTranscriber" else _logger_instance

    # Create formatter
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)-8s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    _logger_instance.addHandler(console_handler)

    # File handler (rotating, max 5MB, keep 3 backups)
    log_file = log_dir / "freetranscriber.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    _logger_instance.addHandler(file_handler)

    # Return child logger if specific name requested
    return _logger_instance.getChild(name) if name != "FreeTranscriber" else _logger_instance


def reset_logger() -> None:
    """
    Reset the logger instance (useful for testing).
    Removes all handlers and resets the global instance.
    """
    global _logger_instance
    if _logger_instance is not None:
        # Remove all handlers
        for handler in _logger_instance.handlers[:]:
            handler.close()
            _logger_instance.removeHandler(handler)
        _logger_instance = None
