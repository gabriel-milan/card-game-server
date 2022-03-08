from typing import Any

from loguru import logger


def log(msg: Any, level: str = "info") -> None:
    """
    Logs a message to prefect's logger.
    """
    levels = {
        "debug": logger.debug,
        "info": logger.info,
        "warning": logger.warning,
        "error": logger.error,
        "critical": logger.critical,
    }
    if level not in levels:
        raise ValueError(f"Invalid log level: {level}")
    levels[level](msg)
