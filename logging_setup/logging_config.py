"""Centralized Loguru configuration for file and console logging."""

from loguru import logger
from pathlib import Path
import sys


def setup_logging(app_name: str = "app"):
    """Configure and return the shared application logger."""
    log_dir = Path(__file__).parent.parent / "logs"
    debug_log = log_dir / f"{app_name}_debug.log"
    info_log = log_dir / f"{app_name}.log"
    error_log = log_dir / f"{app_name}_error.log"

    logger.remove()

    logger.add(
        info_log,
        level="INFO",
        rotation="1 MB",
        retention=10
    )


    logger.add(
        debug_log,
        level="DEBUG",
        rotation="1 MB",
        retention=1
    )

    logger.add(
        error_log,
        level="ERROR",
        rotation="1 MB",
        retention=1
    )

    logger.add(
        sys.stdout,
        level="DEBUG",
    )

    return logger
