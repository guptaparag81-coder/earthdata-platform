"""Logging configuration for the application."""

import logging
import sys
from typing import Any

from pythonjsonlogger import jsonlogger

from earthdata.core.config import Settings

_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def configure_logging(settings: Settings) -> None:
    """Configure the root logger based on application settings.

    Uses structured JSON logs when `log_json` is enabled (recommended for
    production), otherwise falls back to a human-readable format for local
    development.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level.upper())

    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(stream=sys.stdout)

    formatter: logging.Formatter
    if settings.log_json:
        formatter = jsonlogger.JsonFormatter(  # type: ignore[no-untyped-call]
            fmt=_LOG_FORMAT,
            rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger"},
        )
    else:
        formatter = logging.Formatter(_LOG_FORMAT)

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Quiet noisy third-party loggers unless debugging.
    if not settings.app_debug:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger."""
    return logging.getLogger(name)


def bind_context(logger: logging.Logger, **context: Any) -> logging.LoggerAdapter[logging.Logger]:
    """Attach static contextual fields (e.g. request_id) to a logger."""
    return logging.LoggerAdapter(logger, context)
