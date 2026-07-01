"""Core infrastructure exports."""

from typing import Any

from mt5forge.core.constants import (
    ConflictPolicy,
    HealthStatus,
    OrderType,
    SessionStatus,
    SignalDirection,
    SpreadState,
    StrategyStatus,
    Timeframe,
    TradeState,
)
from mt5forge.core.events import (
    BaseEvent,
    ConnectionLost,
    ConnectionRestored,
    EventBus,
    EventType,
    RegimeChanged,
    RiskRejected,
)
from mt5forge.core.exceptions import MT5ForgeError

__all__ = [
    "BaseEvent",
    "ConflictPolicy",
    "ConnectionLost",
    "ConnectionRestored",
    "EventBus",
    "EventType",
    "HealthStatus",
    "MT5ForgeError",
    "OrderType",
    "RegimeChanged",
    "RiskRejected",
    "SessionStatus",
    "SignalDirection",
    "SpreadState",
    "StrategyStatus",
    "Timeframe",
    "TradeState",
    "TradingEngine",
]


def __getattr__(name: str) -> Any:
    if name == "TradingEngine":
        from mt5forge.core.engine import TradingEngine

        return TradingEngine
    raise AttributeError(name)
