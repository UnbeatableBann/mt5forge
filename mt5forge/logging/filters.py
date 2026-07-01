"""Logging filters."""

from __future__ import annotations

import logging


class LevelFilter(logging.Filter):
    """Allow records at or above a configured level."""

    def __init__(self, level: int | str) -> None:
        super().__init__()
        self.level = logging.getLevelName(level) if isinstance(level, str) else level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno >= int(self.level)
