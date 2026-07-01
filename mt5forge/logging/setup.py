"""Structured logging setup."""

from __future__ import annotations

import logging
from typing import Any

from mt5forge.config.trading_config import LoggingConfig
from mt5forge.logging.handlers import build_handlers

try:
    import structlog
except ModuleNotFoundError:
    structlog = None  # type: ignore[assignment]


def configure_logging(config: LoggingConfig | None = None) -> logging.Logger:
    resolved = config or LoggingConfig()
    level = getattr(logging, resolved.level.upper(), logging.INFO)
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    for handler in build_handlers(resolved):
        handler.setLevel(level)
        root.addHandler(handler)
    if structlog is not None:
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer() if resolved.json_logs else structlog.dev.ConsoleRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(level),
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
    return logging.getLogger("mt5forge")


def get_logger(name: str, **context: Any) -> Any:
    if structlog is not None:
        return structlog.get_logger(name).bind(**context)
    logger = logging.getLogger(name)
    return logging.LoggerAdapter(logger, context) if context else logger
