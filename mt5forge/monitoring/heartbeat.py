"""Strategy heartbeat monitoring."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta


class StrategyHeartbeat:
    """Track last activity per strategy and report stale heartbeats."""

    def __init__(self, timeout_seconds: int = 30) -> None:
        self.timeout = timedelta(seconds=timeout_seconds)
        self._beats: dict[str, datetime] = {}

    def beat(self, strategy_name: str) -> None:
        self._beats[strategy_name] = datetime.now(UTC)

    def stale(self, now: datetime | None = None) -> list[str]:
        moment = now or datetime.now(UTC)
        return [name for name, last in self._beats.items() if moment - last > self.timeout]
