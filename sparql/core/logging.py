"""Logging configuration using structlog.

Logs go to stderr to keep stdout clean for data output (piping).
"""

import logging
import sys
from typing import Any

import structlog

# Map log level names to numeric values
_LOG_LEVELS: dict[str, int] = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


def setup_logging(verbose: bool = False) -> None:
    log_level = "debug" if verbose else "info"

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty()),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(_LOG_LEVELS[log_level]),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> Any:
    logger = structlog.get_logger()
    if name:
        logger = logger.bind(logger=name)
    return logger
