"""Hedge lot balancing for no-profit-no-loss recovery."""

from __future__ import annotations

import math

from mt5forge.positions import PnLCalculator


class HedgeCalculator:
    """Calculate counter-trade lot size required to neutralize projected loss."""

    def __init__(self, min_lot: float = 0.01, max_lot: float = 100.0, lot_step: float = 0.01) -> None:
        self.min_lot = min_lot
        self.max_lot = max_lot
        self.lot_step = lot_step
        self.pnl = PnLCalculator()

    def calculate_hedge_lot(
        self,
        original_lot: float,
        original_entry: float,
        current_price: float,
        original_direction: str,
        symbol: str,
    ) -> float:
        direction = original_direction.upper()
        adverse_distance = abs(original_entry - current_price)
        if adverse_distance <= 0 or original_lot <= 0:
            return self._normalize(original_lot)
        if direction == "BUY":
            target_exit = current_price - adverse_distance
            original_pips = (target_exit - original_entry) / self.pnl.pip_size(symbol)
            hedge_pips = (current_price - target_exit) / self.pnl.pip_size(symbol)
        else:
            target_exit = current_price + adverse_distance
            original_pips = (original_entry - target_exit) / self.pnl.pip_size(symbol)
            hedge_pips = (target_exit - current_price) / self.pnl.pip_size(symbol)
        original_loss = abs(original_pips) * original_lot
        required = original_loss / max(abs(hedge_pips), 1e-9)
        return self._normalize(required)

    def breakeven_price(self, buy_lots: float, buy_avg: float, sell_lots: float, sell_avg: float) -> float:
        net_lots = buy_lots - sell_lots
        if abs(net_lots) < 1e-9:
            return (buy_avg + sell_avg) / 2.0
        return ((buy_lots * buy_avg) - (sell_lots * sell_avg)) / net_lots

    def _normalize(self, lot: float) -> float:
        bounded = min(max(lot, self.min_lot), self.max_lot)
        steps = math.ceil(bounded / self.lot_step)
        return round(steps * self.lot_step, 8)
