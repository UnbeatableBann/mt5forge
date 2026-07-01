"""Discord notification channel."""

from __future__ import annotations

from typing import Any

import httpx

from mt5forge.notifications.base import Alert, NotificationChannel
from mt5forge.notifications.formatter import AlertFormatter


class DiscordChannel(NotificationChannel):
    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.formatter = AlertFormatter()

    async def send(self, alert: Alert) -> bool:
        webhook_url = getattr(self.config, "webhook_url", "")
        if not webhook_url:
            return False
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_url, json={"content": self.formatter.text(alert)})
        return 200 <= response.status_code < 300
