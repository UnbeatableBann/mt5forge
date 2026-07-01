"""Rotating file and JSON logging handlers."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from mt5forge.config.trading_config import LoggingConfig


class JsonLineFormatter(logging.Formatter):
    """Format records as JSON lines for analytics ingestion."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in logging.LogRecord("", 0, "", 0, "", (), None).__dict__:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, sort_keys=True)


def build_handlers(config: LoggingConfig) -> list[logging.Handler]:
    log_dir = Path(config.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))

    trading = RotatingFileHandler(
        log_dir / "trading.log",
        maxBytes=config.max_bytes,
        backupCount=config.backup_count,
        encoding="utf-8",
    )
    trading.setFormatter(JsonLineFormatter() if config.json_logs else logging.Formatter("%(message)s"))

    errors = RotatingFileHandler(
        log_dir / "errors.log",
        maxBytes=config.max_bytes,
        backupCount=config.backup_count,
        encoding="utf-8",
    )
    errors.setLevel(logging.ERROR)
    errors.setFormatter(JsonLineFormatter())

    orders = RotatingFileHandler(
        log_dir / "orders.log",
        maxBytes=config.max_bytes * 5,
        backupCount=max(config.backup_count, 10),
        encoding="utf-8",
    )
    orders.setFormatter(JsonLineFormatter())

    trades = RotatingFileHandler(
        log_dir / "trades.jsonl",
        maxBytes=config.max_bytes,
        backupCount=config.backup_count,
        encoding="utf-8",
    )
    trades.setFormatter(JsonLineFormatter())

    return [console, trading, errors, orders, trades]
