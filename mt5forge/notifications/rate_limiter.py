"""Notification flood protection."""

from __future__ import annotations

import time

from mt5forge.notifications.alert_types import AlertType


class NotificationRateLimiter:
    """Per-alert-type cooldown limiter."""

    default_limits: dict[AlertType, int] = {
        AlertType.MT5_DISCONNECTED: 60,
        AlertType.ABNORMAL_SPREAD: 30,
        AlertType.DRAWDOWN_WARNING: 300,
    }

    def __init__(self, limits: dict[AlertType | str, int] | None = None) -> None:
        self.limits: dict[AlertType, int] = dict(self.default_limits)
        for key, value in (limits or {}).items():
            alert_type = key if isinstance(key, AlertType) else AlertType(str(key))
            self.limits[alert_type] = value
        self._last_sent: dict[AlertType, float] = {}

    def allow(self, alert_type: AlertType) -> bool:
        limit = self.limits.get(alert_type, 0)
        now = time.monotonic()
        last = self._last_sent.get(alert_type, 0.0)
        if limit <= 0 or now - last >= limit:
            self._last_sent[alert_type] = now
            return True
        return False
