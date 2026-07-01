"""Time-based trade management."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from mt5forge.orders import OrderManager


@dataclass(slots=True, frozen=True)
class TimedTrade:
    ticket: int
    close_after: datetime


class TradeTimer:
    """Track positions that should be closed after a deadline."""

    def __init__(self, order_manager: OrderManager) -> None:
        self.order_manager = order_manager
        self._timers: dict[int, TimedTrade] = {}

    def register(self, ticket: int, duration: timedelta) -> None:
        self._timers[ticket] = TimedTrade(ticket=ticket, close_after=datetime.now(UTC) + duration)

    def close_expired(self, now: datetime | None = None) -> list[int]:
        moment = now or datetime.now(UTC)
        closed: list[int] = []
        for ticket, timed in list(self._timers.items()):
            if moment >= timed.close_after and self.order_manager.close_order(ticket):
                closed.append(ticket)
                self._timers.pop(ticket, None)
        return closed
