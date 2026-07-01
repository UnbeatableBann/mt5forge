"""Alert formatting."""

from __future__ import annotations

import json

from mt5forge.notifications.base import Alert


class AlertFormatter:
    """Format alerts for human or machine-readable channels."""

    def text(self, alert: Alert) -> str:
        parts = [f"[{alert.severity.value}] {alert.title}", alert.message]
        if alert.symbol:
            parts.append(f"symbol={alert.symbol}")
        if alert.ticket:
            parts.append(f"ticket={alert.ticket}")
        return " | ".join(parts)

    def json(self, alert: Alert) -> str:
        return json.dumps(
            {
                "alert_type": alert.alert_type.value,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "symbol": alert.symbol,
                "ticket": alert.ticket,
                "metadata": alert.metadata,
                "timestamp": alert.timestamp.isoformat(),
            },
            default=str,
            sort_keys=True,
        )
