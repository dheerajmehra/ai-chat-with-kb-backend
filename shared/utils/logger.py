"""Logging configuration."""
from loguru import logger
import sys
from shared.config import get_settings

settings = get_settings()

# Remove default handler
logger.remove()

# Add custom handler
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.log_level,
    colorize=True
)

logger.add(
    "logs/ingestion_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="30 days",
    level=settings.log_level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
)

