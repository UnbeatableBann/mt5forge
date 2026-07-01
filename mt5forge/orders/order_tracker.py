"""Order state tracking."""

from __future__ import annotations

import threading

from mt5forge.orders.order_builder import OrderResult


class OrderTracker:
    """Thread-safe in-memory order result cache."""

    def __init__(self) -> None:
        self._orders: dict[int, OrderResult] = {}
        self._lock = threading.RLock()

    def record(self, result: OrderResult) -> None:
        if result.ticket is not None:
            with self._lock:
                self._orders[result.ticket] = result

    def get(self, ticket: int) -> OrderResult | None:
        with self._lock:
            result = self._orders.get(ticket)
        return result

    def all(self) -> list[OrderResult]:
        with self._lock:
            results = list(self._orders.values())
        return results
