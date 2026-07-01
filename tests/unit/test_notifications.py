from __future__ import annotations

import pytest

from mt5forge.notifications import Alert, AlertSeverity, AlertType, NotificationBus, NotificationChannel


class CollectingChannel(NotificationChannel):
    def __init__(self):
        super().__init__()
        self.alerts: list[Alert] = []

    async def send(self, alert: Alert) -> bool:
        self.alerts.append(alert)
        return True


@pytest.mark.asyncio
async def test_notification_bus_sync_delivery():
    channel = CollectingChannel()
    bus = NotificationBus()
    bus.register_channel(channel)
    bus.emit_sync(Alert(AlertType.TRADE_OPENED, AlertSeverity.INFO, "Opened", "Trade opened"))
    assert len(channel.alerts) == 1
