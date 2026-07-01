"""Partial close manager."""

from __future__ import annotations

from mt5forge.orders import OrderManager


class PartialCloseManager:
    """Close part of an open position while preserving lifecycle safety."""

    def __init__(self, order_manager: OrderManager) -> None:
        self.order_manager = order_manager

    def close_partial(self, ticket: int, lot: float) -> bool:
        if lot <= 0:
            return False
        return self.order_manager.close_order(ticket, lot=lot)
