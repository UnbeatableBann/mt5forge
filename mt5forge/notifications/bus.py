"""Async notification dispatcher."""

from __future__ import annotations

import asyncio
import threading

from mt5forge.config.notification_config import NotificationConfig
from mt5forge.notifications.base import Alert, NotificationChannel
from mt5forge.notifications.rate_limiter import NotificationRateLimiter


class NotificationBus:
    """Central non-blocking notification dispatcher."""

    def __init__(
        self,
        config: NotificationConfig | None = None,
        rate_limiter: NotificationRateLimiter | None = None,
    ) -> None:
        self.config = config or NotificationConfig()
        self.rate_limiter = rate_limiter or NotificationRateLimiter(self.config.rate_limits)
        self.channels: list[NotificationChannel] = []
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None

    def register_channel(self, channel: NotificationChannel) -> None:
        self.channels.append(channel)

    def emit(self, alert: Alert) -> None:
        if not self.config.enabled or not self.rate_limiter.allow(alert.alert_type):
            return
        loop = self._ensure_loop()
        loop.call_soon_threadsafe(lambda: asyncio.create_task(self._deliver(alert)))

    def emit_sync(self, alert: Alert) -> None:
        if not self.config.enabled or not self.rate_limiter.allow(alert.alert_type):
            return
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(self._deliver(alert))
        else:
            thread = threading.Thread(
                target=lambda: asyncio.run(self._deliver(alert)),
                name="mt5forge-notification-sync",
            )
            thread.start()
            thread.join()

    async def _deliver(self, alert: Alert) -> None:
        tasks = [channel.send(alert) for channel in self.channels if channel.accepts(alert)]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def _ensure_loop(self) -> asyncio.AbstractEventLoop:
        if self._loop and self._loop.is_running():
            return self._loop

        loop = asyncio.new_event_loop()
        self._loop = loop

        def runner() -> None:
            asyncio.set_event_loop(loop)
            loop.run_forever()

        self._thread = threading.Thread(
            target=runner,
            name="mt5forge-notifications",
            daemon=True,
        )
        self._thread.start()

        return loop
