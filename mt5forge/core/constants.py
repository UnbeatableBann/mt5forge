"""Shared enums and defaults used across MT5Forge."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

DEFAULT_MAGIC_BASE = 10000
DEFAULT_DEVIATION_POINTS = 10
DEFAULT_PIP_SIZE = 0.0001
JPY_PIP_SIZE = 0.01


class Timeframe(StrEnum):
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    M30 = "M30"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"
    W1 = "W1"
    MN1 = "MN1"

    def to_mt5(self, mt5: Any) -> int:
        attr = f"TIMEFRAME_{self.value}"
        if hasattr(mt5, attr):
            return int(getattr(mt5, attr))
        fallback = {
            Timeframe.M1: 1,
            Timeframe.M5: 5,
            Timeframe.M15: 15,
            Timeframe.M30: 30,
            Timeframe.H1: 60,
            Timeframe.H4: 240,
            Timeframe.D1: 1440,
            Timeframe.W1: 10080,
            Timeframe.MN1: 43200,
        }
        return fallback[self]

    @classmethod
    def parse(cls, value: str | Timeframe) -> Timeframe:
        if isinstance(value, Timeframe):
            return value
        normalized = value.upper()
        if normalized in cls.__members__:
            return cls[normalized]
        return cls(normalized)


class OrderType(StrEnum):
    BUY = "BUY"
    SELL = "SELL"
    BUY_LIMIT = "BUY_LIMIT"
    SELL_LIMIT = "SELL_LIMIT"
    BUY_STOP = "BUY_STOP"
    SELL_STOP = "SELL_STOP"
    BUY_STOP_LIMIT = "BUY_STOP_LIMIT"
    SELL_STOP_LIMIT = "SELL_STOP_LIMIT"

    @property
    def is_buy(self) -> bool:
        return self.name.startswith("BUY")

    @property
    def is_sell(self) -> bool:
        return self.name.startswith("SELL")

    @property
    def is_pending(self) -> bool:
        return self not in {OrderType.BUY, OrderType.SELL}

    def opposite_market(self) -> OrderType:
        return OrderType.SELL if self.is_buy else OrderType.BUY


class SignalDirection(StrEnum):
    BUY = "BUY"
    SELL = "SELL"
    CLOSE = "CLOSE"
    HOLD = "HOLD"

    def to_order_type(self) -> OrderType:
        if self == SignalDirection.BUY:
            return OrderType.BUY
        if self == SignalDirection.SELL:
            return OrderType.SELL
        raise ValueError(f"{self.value} cannot be converted to a market order")


class StrategyStatus(StrEnum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    DISABLED = "disabled"


class SessionStatus(StrEnum):
    AUTHENTICATED = "authenticated"
    INITIALIZED = "initialized"
    DISCONNECTED = "disconnected"
    UNAUTHORIZED = "unauthorized"
    ACCOUNT_SUSPENDED = "account_suspended"
    UNKNOWN = "unknown"


class HealthStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"


class SpreadState(StrEnum):
    NORMAL = "normal"
    ELEVATED = "elevated"
    ABNORMAL = "abnormal"


class ConflictPolicy(StrEnum):
    ALLOW_BOTH = "allow_both"
    REJECT_NEWER = "reject_newer"
    REJECT_ALL = "reject_all"


class TradeState(StrEnum):
    PENDING = "pending"
    PLACED = "placed"
    OPEN = "open"
    MODIFIED = "modified"
    PARTIAL_CLOSE = "partial_close"
    CLOSED = "closed"
