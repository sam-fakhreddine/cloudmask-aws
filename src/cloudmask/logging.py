"""Structured logging for CloudMask."""

import logging
import sys
from pathlib import Path
from typing import Any

# Default logger
logger = logging.getLogger("cloudmask")


def setup_logging(
    level: str = "INFO",
    log_file: Path | None = None,
    debug: bool = False,
) -> None:
    """Configure logging for CloudMask.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for logging
        debug: Enable debug mode with verbose output
    """
    if debug:
        level = "DEBUG"

    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level)

    if debug:
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        formatter = logging.Formatter("%(levelname)s: %(message)s")

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s:%(funcName)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)


def log_operation(operation: str, **kwargs: Any) -> None:
    """Log an operation with structured data."""
    details = " ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.info(f"{operation}: {details}")


def log_error(error: Exception, context: str = "") -> None:
    """Log an error with context."""
    if context:
        logger.error(f"{context}: {error}")
    else:
        logger.error(str(error))
    logger.debug("Error details:", exc_info=True)
