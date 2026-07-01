"""Async email notification channel."""

from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage
from typing import Any

from mt5forge.notifications.base import Alert, NotificationChannel
from mt5forge.notifications.formatter import AlertFormatter


class EmailChannel(NotificationChannel):
    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.formatter = AlertFormatter()

    async def send(self, alert: Alert) -> bool:
        message = EmailMessage()
        sender = getattr(self.config, "from_address", "") or getattr(self.config, "username", "")
        recipient = getattr(self.config, "to_address", "")
        if not sender or not recipient:
            return False
        message["From"] = sender
        message["To"] = recipient
        message["Subject"] = alert.title
        message.set_content(self.formatter.text(alert))
        try:
            import aiosmtplib

            await aiosmtplib.send(
                message,
                hostname=getattr(self.config, "smtp_host", ""),
                port=getattr(self.config, "smtp_port", 587),
                username=getattr(self.config, "username", ""),
                password=getattr(self.config, "password", ""),
                start_tls=getattr(self.config, "use_tls", True),
            )
            return True
        except ModuleNotFoundError:
            return await asyncio.to_thread(self._send_sync, message)

    def _send_sync(self, message: EmailMessage) -> bool:
        host = getattr(self.config, "smtp_host", "")
        port = getattr(self.config, "smtp_port", 587)
        if not host:
            return False
        with smtplib.SMTP(host, port, timeout=10.0) as smtp:
            if getattr(self.config, "use_tls", True):
                smtp.starttls()
            username = getattr(self.config, "username", "")
            password = getattr(self.config, "password", "")
            if username and password:
                smtp.login(username, password)
            smtp.send_message(message)
        return True
