from __future__ import annotations

from mt5forge.notifications import Alert, AlertSeverity, AlertType, NotificationBus
from mt5forge.notifications.channels import ConsoleChannel

if __name__ == "__main__":
    bus = NotificationBus()
    bus.register_channel(ConsoleChannel())
    bus.emit_sync(Alert(AlertType.MT5_RECONNECTED, AlertSeverity.INFO, "Connected", "MT5 session restored"))
