# src/assistant/utils/logging.py
import os
import sys

from loguru import logger

from assistant.config import settings


def setup_logger():
    """Configures the Loguru logger for the application."""
    logger.remove()  # Remove default handler to avoid duplicates
    stream = sys.stdout if "PYTEST_CURRENT_TEST" in os.environ else sys.stderr
    logger.add(
        stream,
        level=settings.LOG_LEVEL,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
            "<level>{message}</level>"
        ),
    )


# Configure the logger as soon as this module is imported
setup_logger()
