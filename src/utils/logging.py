"""Logging configuration utilities for the WSP Sniper application.

This module provides:
- setup_logger: configures the Loguru logger with console and file outputs.
"""

import sys

from loguru import logger


def setup_logger(level: str = "INFO", log_file: str = "logs/wsp_sniper.log"):
    """Configures the Loguru logger.

    Args:
        level: Minimum log level for the console (default: INFO).
        log_file: Path to the log file for persistent storage.
    """
    logger.remove()

    logger.add(
        sys.stderr,
        format=(
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | <level>{message}</level>"
        ),
        level=level,
        colorize=True,
    )

    if log_file:
        file_format = (
            "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
            "{name}:{function}:{line} - {message}"
        )
        logger.add(
            log_file,
            rotation="10 MB",
            retention="5 days",
            compression="zip",
            format=file_format,
            level="DEBUG",
            enqueue=True,
        )
