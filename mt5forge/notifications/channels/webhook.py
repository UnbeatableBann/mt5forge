"""Generic webhook notification channel."""

from __future__ import annotations

import httpx

from mt5forge.notifications.base import Alert, NotificationChannel


class WebhookChannel(NotificationChannel):
    async def send(self, alert: Alert) -> bool:
        url = getattr(self.config, "url", "")
        headers = getattr(self.config, "headers", {})
        if not url:
            return False
        payload = {
            "type": alert.alert_type.value,
            "severity": alert.severity.value,
            "title": alert.title,
            "message": alert.message,
            "symbol": alert.symbol,
            "ticket": alert.ticket,
            "metadata": alert.metadata,
            "timestamp": alert.timestamp.isoformat(),
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
        return 200 <= response.status_code < 300
