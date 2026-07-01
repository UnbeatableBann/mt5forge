"""Console notification channel."""

from __future__ import annotations

import asyncio
from typing import Any

from mt5forge.notifications.base import Alert, NotificationChannel
from mt5forge.notifications.formatter import AlertFormatter


class ConsoleChannel(NotificationChannel):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.formatter = AlertFormatter()

    async def send(self, alert: Alert) -> bool:
        await asyncio.to_thread(print, self.formatter.text(alert))
        return True
