"""MT5 terminal connector."""

from __future__ import annotations

import importlib
import threading
import time
from dataclasses import dataclass
from typing import Any

from mt5forge.core.events import ConnectionLost, ConnectionRestored, EventBus
from mt5forge.core.exceptions import AuthenticationError, ConnectionError
from mt5forge.logging import get_logger


@dataclass(slots=True, frozen=True)
class MT5Credentials:
    account: int
    password: str
    server: str


class MT5Connector:
    """Manage MT5 terminal initialization, login, shutdown, and reconnect."""

    def __init__(
        self,
        terminal_path: str = "",
        event_bus: EventBus | None = None,
        reconnect_attempts: int = 20,
        reconnect_delay_base: float = 2.0,
        reconnect_delay_max: float = 30.0,
        mt5: Any | None = None,
    ) -> None:
        self.terminal_path = terminal_path
        self.event_bus = event_bus or EventBus()
        self.reconnect_attempts = reconnect_attempts
        self.reconnect_delay_base = reconnect_delay_base
        self.reconnect_delay_max = reconnect_delay_max
        self._mt5 = mt5
        self._initialized = False
        self._credentials: MT5Credentials | None = None
        self._lock = threading.RLock()
        self.logger = get_logger(__name__)

    @property
    def mt5(self) -> Any:
        if self._mt5 is None:
            try:
                self._mt5 = importlib.import_module("MetaTrader5")
            except ModuleNotFoundError as exc:
                raise ConnectionError("The official MetaTrader5 package is required for live MT5 operations") from exc
        return self._mt5

    def initialize(self) -> bool:
        with self._lock:
            try:
                ok = bool(self.mt5.initialize(path=self.terminal_path)) if self.terminal_path else bool(self.mt5.initialize())
            except Exception as exc:
                raise ConnectionError(f"MT5 initialization failed: {exc}") from exc
            self._initialized = ok
            if not ok:
                last_error = self._last_error()
                raise ConnectionError(f"MT5 initialization returned false: {last_error}")
            self.logger.info("mt5_initialized", extra={"terminal_path": self.terminal_path})
            return ok

    def login(self, credentials: MT5Credentials) -> bool:
        with self._lock:
            if not self._initialized:
                self.initialize()
            try:
                ok = bool(
                    self.mt5.login(
                        credentials.account,
                        password=credentials.password,
                        server=credentials.server,
                    )
                )
            except Exception as exc:
                raise AuthenticationError(f"MT5 login failed: {exc}") from exc
            if not ok:
                raise AuthenticationError(f"MT5 login returned false: {self._last_error()}")
            self._credentials = credentials
            self.logger.info(
                "mt5_login_success",
                extra={"account": credentials.account, "server": credentials.server},
            )
            self.event_bus.publish(ConnectionRestored(source=__name__))
            return ok

    def shutdown(self) -> None:
        with self._lock:
            if self._mt5 is not None:
                try:
                    self._mt5.shutdown()
                except Exception as exc:
                    self.logger.warning("mt5_shutdown_failed", extra={"error": str(exc)})
            self._initialized = False

    def is_connected(self) -> bool:
        with self._lock:
            if not self._initialized:
                return False
            try:
                terminal = self.mt5.terminal_info()
                account = self.mt5.account_info()
            except Exception:
                return False
            return bool(terminal and account)

    def reconnect(self) -> bool:
        credentials = self._credentials
        if credentials is None:
            return False
        self.event_bus.publish(ConnectionLost(source=__name__, reason="manual_or_health_reconnect"))
        for attempt in range(1, self.reconnect_attempts + 1):
            delay = min(self.reconnect_delay_base * (2 ** (attempt - 1)), self.reconnect_delay_max)
            self.shutdown()
            try:
                self.initialize()
                if self.login(credentials):
                    self.event_bus.publish(ConnectionRestored(source=__name__))
                    return True
            except ConnectionError as exc:
                self.logger.warning(
                    "mt5_reconnect_attempt_failed",
                    extra={"attempt": attempt, "error": str(exc), "delay": delay},
                )
            time.sleep(delay)
        self.event_bus.publish(ConnectionLost(source=__name__, reason="reconnect_attempts_exhausted"))
        return False

    def _last_error(self) -> Any:
        try:
            return self.mt5.last_error()
        except Exception:
            return "unknown"
