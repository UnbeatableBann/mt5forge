"""Broker and internet health monitoring."""

from __future__ import annotations

import socket
import threading
from collections.abc import Callable

from mt5forge.connection.connector import MT5Connector
from mt5forge.core.constants import HealthStatus
from mt5forge.core.events import ConnectionLost, EventBus
from mt5forge.logging import get_logger


class BrokerHealthMonitor:
    """Background broker connectivity monitor."""

    def __init__(
        self,
        connector: MT5Connector,
        event_bus: EventBus | None = None,
        interval_seconds: float = 10.0,
        internet_host: str = "1.1.1.1",
        internet_port: int = 53,
        internet_timeout_seconds: float = 2.0,
    ) -> None:
        self.connector = connector
        self.event_bus = event_bus or connector.event_bus
        self.interval_seconds = interval_seconds
        self.internet_host = internet_host
        self.internet_port = internet_port
        self.internet_timeout_seconds = internet_timeout_seconds
        self.status = HealthStatus.CRITICAL
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._callbacks: list[Callable[[HealthStatus], None]] = []
        self.logger = get_logger(__name__)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="mt5forge-broker-health", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=self.interval_seconds + 1.0)

    def subscribe(self, callback: Callable[[HealthStatus], None]) -> None:
        self._callbacks.append(callback)

    def check_once(self) -> HealthStatus:
        internet_ok = self._internet_available()
        connected = self.connector.is_connected()
        if connected and internet_ok:
            status = HealthStatus.HEALTHY
        elif internet_ok:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.CRITICAL
        if status != self.status:
            self.status = status
            self.logger.info("broker_health_changed", extra={"status": status.value})
            for callback in list(self._callbacks):
                callback(status)
            if status != HealthStatus.HEALTHY:
                self.event_bus.publish(ConnectionLost(source=__name__, reason=status.value))
        return status

    def _run(self) -> None:
        while not self._stop.wait(self.interval_seconds):
            self.check_once()

    def _internet_available(self) -> bool:
        try:
            with socket.create_connection(
                (self.internet_host, self.internet_port),
                timeout=self.internet_timeout_seconds,
            ):
                return True
        except OSError:
            return False
