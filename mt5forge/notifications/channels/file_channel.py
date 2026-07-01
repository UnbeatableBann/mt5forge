"""File notification channel."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from mt5forge.notifications.base import Alert, NotificationChannel
from mt5forge.notifications.formatter import AlertFormatter


class FileChannel(NotificationChannel):
    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.formatter = AlertFormatter()

    async def send(self, alert: Alert) -> bool:
        path = Path(getattr(self.config, "path", "logs/alerts.jsonl"))
        path.parent.mkdir(parents=True, exist_ok=True)
        line = self.formatter.json(alert) + "\n"
        await asyncio.to_thread(self._append, path, line)
        return True

    @staticmethod
    def _append(path: Path, line: str) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)
