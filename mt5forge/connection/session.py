"""Broker session validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mt5forge.connection.connector import MT5Connector
from mt5forge.core.constants import SessionStatus
from mt5forge.core.exceptions import SessionError


@dataclass(slots=True, frozen=True)
class AccountInfo:
    login: int
    server: str
    balance: float
    equity: float
    margin: float
    free_margin: float
    margin_level: float
    currency: str
    trade_allowed: bool

    @classmethod
    def from_mt5(cls, raw: Any) -> AccountInfo:
        data = raw._asdict() if hasattr(raw, "_asdict") else dict(raw)
        return cls(
            login=int(data.get("login", 0)),
            server=str(data.get("server", "")),
            balance=float(data.get("balance", 0.0)),
            equity=float(data.get("equity", 0.0)),
            margin=float(data.get("margin", 0.0)),
            free_margin=float(data.get("margin_free", data.get("free_margin", 0.0))),
            margin_level=float(data.get("margin_level", 0.0)),
            currency=str(data.get("currency", "USD")),
            trade_allowed=bool(data.get("trade_allowed", True)),
        )


class SessionManager:
    """Validate broker account state and session integrity."""

    def __init__(self, connector: MT5Connector) -> None:
        self.connector = connector

    def validate_session(self) -> SessionStatus:
        if not self.connector.is_connected():
            return SessionStatus.DISCONNECTED
        try:
            account = self.get_account_info()
        except SessionError:
            return SessionStatus.UNAUTHORIZED
        if not account.trade_allowed:
            return SessionStatus.ACCOUNT_SUSPENDED
        return SessionStatus.AUTHENTICATED

    def get_account_info(self) -> AccountInfo:
        try:
            raw = self.connector.mt5.account_info()
        except Exception as exc:
            raise SessionError(f"Could not read account info: {exc}") from exc
        if not raw:
            raise SessionError("MT5 account_info returned no account data")
        return AccountInfo.from_mt5(raw)
