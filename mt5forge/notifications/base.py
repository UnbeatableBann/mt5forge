"""Alert model and channel base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from mt5forge.notifications.alert_types import AlertSeverity, AlertType


@dataclass(slots=True)
class Alert:
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    symbol: str | None = None
    ticket: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


class NotificationChannel(ABC):
    """Base class for async notification channels."""

    def __init__(self, config: Any | None = None) -> None:
        self.config = config

    @property
    def enabled(self) -> bool:
        return bool(getattr(self.config, "enabled", True))

    def accepts(self, alert: Alert) -> bool:
        min_severity = getattr(self.config, "min_severity", "INFO")
        configured = AlertSeverity[min_severity.upper()] if isinstance(min_severity, str) else min_severity
        return self.enabled and alert.severity.rank >= configured.rank

    @abstractmethod
    async def send(self, alert: Alert) -> bool:
        return False
