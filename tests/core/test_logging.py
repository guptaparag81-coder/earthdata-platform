"""Tests for logging configuration."""

import logging

from earthdata.core.config import Settings
from earthdata.core.logging import bind_context, configure_logging, get_logger


def test_configure_logging_plain_format() -> None:
    settings = Settings(log_level="DEBUG", log_json=False, app_debug=True)

    configure_logging(settings)

    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG
    assert len(root_logger.handlers) == 1
    assert isinstance(root_logger.handlers[0].formatter, logging.Formatter)


def test_configure_logging_json_format() -> None:
    settings = Settings(log_level="INFO", log_json=True, app_debug=False)

    configure_logging(settings)

    root_logger = logging.getLogger()
    assert root_logger.level == logging.INFO
    assert len(root_logger.handlers) == 1
    assert logging.getLogger("uvicorn.access").level == logging.WARNING
    assert logging.getLogger("httpx").level == logging.WARNING


def test_get_logger_returns_named_logger() -> None:
    logger = get_logger("earthdata.test")
    assert logger.name == "earthdata.test"


def test_bind_context_attaches_extra_fields() -> None:
    logger = get_logger("earthdata.test")
    adapter = bind_context(logger, request_id="abc-123")

    assert adapter.extra == {"request_id": "abc-123"}
    assert adapter.logger is logger
