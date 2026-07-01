"""Telegram notification channel."""

from __future__ import annotations

from typing import Any

import httpx

from mt5forge.notifications.base import Alert, NotificationChannel
from mt5forge.notifications.formatter import AlertFormatter


class TelegramChannel(NotificationChannel):
    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.formatter = AlertFormatter()

    async def send(self, alert: Alert) -> bool:
        token = getattr(self.config, "bot_token", "")
        chat_id = getattr(self.config, "chat_id", "")
        if not token or not chat_id:
            return False
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json={"chat_id": chat_id, "text": self.formatter.text(alert)})
        return response.status_code == 200
