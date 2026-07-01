"""Main system watchdog."""

from __future__ import annotations

import socket
import threading

from mt5forge.connection import BrokerHealthMonitor, MT5Connector
from mt5forge.monitoring.heartbeat import StrategyHeartbeat
from mt5forge.monitoring.latency_tracker import ExecutionLatencyTracker
from mt5forge.monitoring.resource_monitor import ResourceMonitor
from mt5forge.monitoring.terminal_watcher import MT5TerminalWatcher
from mt5forge.notifications import Alert, AlertSeverity, AlertType, NotificationBus


class SystemMonitor:
    """Dedicated watchdog for terminal, broker, internet, resources, and heartbeat."""

    def __init__(
        self,
        connector: MT5Connector,
        notification_bus: NotificationBus | None = None,
        interval_seconds: float = 5.0,
    ) -> None:
        self.connector = connector
        self.notification_bus = notification_bus or NotificationBus()
        self.interval_seconds = interval_seconds
        self.terminal_watcher = MT5TerminalWatcher(connector)
        self.broker_monitor = BrokerHealthMonitor(connector)
        self.latency_tracker = ExecutionLatencyTracker()
        self.resource_monitor = ResourceMonitor()
        self.heartbeat = StrategyHeartbeat()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="mt5forge-system-monitor", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=self.interval_seconds + 1.0)

    def check_once(self) -> dict[str, bool]:
        terminal_alive = self.terminal_watcher.alive()
        internet_ok = self._internet_ok()
        resources = self.resource_monitor.snapshot()
        stale = self.heartbeat.stale()
        if not terminal_alive:
            self.notification_bus.emit(Alert(AlertType.TERMINAL_FROZEN, AlertSeverity.CRITICAL, "MT5 terminal unavailable", "Terminal info could not be read"))
        if not internet_ok:
            self.notification_bus.emit(Alert(AlertType.MT5_DISCONNECTED, AlertSeverity.CRITICAL, "Internet unavailable", "Connectivity check failed"))
        if not resources.healthy:
            self.notification_bus.emit(
                Alert(AlertType.STRATEGY_FAILURE, AlertSeverity.WARNING, "Resource threshold exceeded", f"CPU {resources.cpu_percent:.1f}% memory {resources.memory_percent:.1f}%")
            )
        for name in stale:
            self.notification_bus.emit(Alert(AlertType.STRATEGY_FAILURE, AlertSeverity.ERROR, "Strategy heartbeat missed", name))
        return {
            "terminal_alive": terminal_alive,
            "internet_ok": internet_ok,
            "resources_healthy": resources.healthy,
            "heartbeats_ok": not stale,
        }

    def _run(self) -> None:
        while not self._stop.wait(self.interval_seconds):
            self.check_once()

    @staticmethod
    def _internet_ok() -> bool:
        try:
            with socket.create_connection(("1.1.1.1", 53), timeout=2.0):
                return True
        except OSError:
            return False
