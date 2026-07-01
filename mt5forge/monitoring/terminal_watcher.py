"""MT5 terminal watcher."""

from __future__ import annotations

from datetime import UTC, datetime

from mt5forge.connection import MT5Connector


class MT5TerminalWatcher:
    """Detect terminal availability and frozen terminal state."""

    def __init__(self, connector: MT5Connector, frozen_after_seconds: int = 60) -> None:
        self.connector = connector
        self.frozen_after_seconds = frozen_after_seconds
        self.last_seen = datetime.now(UTC)

    def alive(self) -> bool:
        try:
            info = self.connector.mt5.terminal_info()
        except Exception:
            return False
        if info:
            self.last_seen = datetime.now(UTC)
            return True
        return False

    def frozen(self) -> bool:
        self.alive()
        elapsed = datetime.now(UTC) - self.last_seen
        return elapsed.total_seconds() > self.frozen_after_seconds
