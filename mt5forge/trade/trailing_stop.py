"""Trailing stop manager."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from enum import StrEnum

from mt5forge.positions import PnLCalculator, PositionTracker
from mt5forge.trade.tp_sl_manager import TpSlManager


class TrailMode(StrEnum):
    FIXED_PIPS = "fixed_pips"
    ATR_BASED = "atr_based"
    PERCENT_BASED = "percent_based"


@dataclass(slots=True)
class TrailingRule:
    trail_pips: float
    activation_pips: float
    mode: TrailMode = TrailMode.FIXED_PIPS


class TrailingStopManager:
    """Background trailing stop watcher."""

    def __init__(
        self,
        tp_sl_manager: TpSlManager,
        position_tracker: PositionTracker,
        interval_seconds: float = 1.0,
    ) -> None:
        self.tp_sl_manager = tp_sl_manager
        self.position_tracker = position_tracker
        self.interval_seconds = interval_seconds
        self.rules: dict[int, TrailingRule] = {}
        self.pnl = PnLCalculator()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def enable(self, ticket: int, trail_pips: float, activation_pips: float = 0.0) -> None:
        self.rules[ticket] = TrailingRule(trail_pips=trail_pips, activation_pips=activation_pips)

    def disable(self, ticket: int) -> None:
        self.rules.pop(ticket, None)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="mt5forge-trailing-stop", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=self.interval_seconds + 1.0)

    def update_once(self) -> dict[int, bool]:
        outcomes: dict[int, bool] = {}
        for ticket, rule in list(self.rules.items()):
            position = self.position_tracker.get_by_ticket(ticket)
            if position is None:
                self.disable(ticket)
                continue
            direction = "BUY" if position.order_type.is_buy else "SELL"
            profit_pips = self.pnl.calculate_pnl_pips(position.entry_price, position.current_price, direction, position.symbol)
            if profit_pips < rule.activation_pips:
                continue
            pip_size = self.pnl.pip_size(position.symbol)
            new_sl = position.current_price - rule.trail_pips * pip_size if position.order_type.is_buy else position.current_price + rule.trail_pips * pip_size
            outcomes[ticket] = self.tp_sl_manager.modify_sl(ticket, new_sl)
        return outcomes

    def _run(self) -> None:
        while not self._stop.wait(self.interval_seconds):
            self.update_once()
