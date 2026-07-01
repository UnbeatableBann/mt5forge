"""Typed in-process event bus."""

from __future__ import annotations

import asyncio
import inspect
import threading
from collections import defaultdict
from collections.abc import Awaitable, Callable, Coroutine, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, TypeVar


class EventType(StrEnum):
    CONNECTION_LOST = "connection_lost"
    CONNECTION_RESTORED = "connection_restored"
    ORDER_PLACED = "order_placed"
    ORDER_CLOSED = "order_closed"
    RISK_REJECTED = "risk_rejected"
    ALERT_RAISED = "alert_raised"
    REGIME_CHANGED = "regime_changed"
    HEARTBEAT_MISSED = "heartbeat_missed"
    TRADE_STATE_CHANGED = "trade_state_changed"


@dataclass(slots=True, frozen=True)
class BaseEvent:
    event_type: EventType
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    source: str = "mt5forge"
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class ConnectionLost(BaseEvent):
    reason: str = ""
    event_type: EventType = field(default=EventType.CONNECTION_LOST, init=False)


@dataclass(slots=True, frozen=True)
class ConnectionRestored(BaseEvent):
    event_type: EventType = field(default=EventType.CONNECTION_RESTORED, init=False)


@dataclass(slots=True, frozen=True)
class OrderPlaced(BaseEvent):
    ticket: int = 0
    symbol: str = ""
    event_type: EventType = field(default=EventType.ORDER_PLACED, init=False)


@dataclass(slots=True, frozen=True)
class OrderClosed(BaseEvent):
    ticket: int = 0
    symbol: str = ""
    profit: float = 0.0
    event_type: EventType = field(default=EventType.ORDER_CLOSED, init=False)


@dataclass(slots=True, frozen=True)
class RiskRejected(BaseEvent):
    symbol: str = ""
    reason: str = ""
    event_type: EventType = field(default=EventType.RISK_REJECTED, init=False)


@dataclass(slots=True, frozen=True)
class RegimeChanged(BaseEvent):
    symbol: str = ""
    old_regime: str = ""
    new_regime: str = ""
    event_type: EventType = field(default=EventType.REGIME_CHANGED, init=False)


EventT = TypeVar("EventT", bound=BaseEvent)
EventHandler = Callable[[EventT], None | Awaitable[None]]


class EventBus:
    """Thread-safe typed pub/sub bus for infrastructure events."""

    def __init__(self) -> None:
        self._handlers: dict[type[BaseEvent], list[EventHandler[Any]]] = defaultdict(list)
        self._lock = threading.RLock()

    def subscribe(self, event_cls: type[EventT], handler: EventHandler[EventT]) -> None:
        with self._lock:
            self._handlers[event_cls].append(handler)

    def unsubscribe(self, event_cls: type[EventT], handler: EventHandler[EventT]) -> None:
        with self._lock:
            handlers = self._handlers.get(event_cls, [])
            self._handlers[event_cls] = [item for item in handlers if item is not handler]

    def publish(self, event: EventT) -> None:
        for handler in self._matching_handlers(event):
            result = handler(event)
            if inspect.isawaitable(result):
                self._run_awaitable(result)

    async def publish_async(self, event: EventT) -> None:
        awaitables: list[Awaitable[None]] = []
        for handler in self._matching_handlers(event):
            result = handler(event)
            if inspect.isawaitable(result):
                awaitables.append(result)
        if awaitables:
            await asyncio.gather(*awaitables)

    def _matching_handlers(self, event: BaseEvent) -> list[EventHandler[Any]]:
        event_cls = type(event)
        with self._lock:
            handlers = list(self._handlers.get(event_cls, []))
            handlers.extend(self._handlers.get(BaseEvent, []))
        return handlers

    @staticmethod
    def _run_awaitable(awaitable: Coroutine[Any, Any, None] | Awaitable[None]) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            if isinstance(awaitable, Coroutine):
                asyncio.run(awaitable)
            else:
                asyncio.run(awaitable)  # type: ignore
        else:
            loop.create_task(awaitable)  # type: ignore
