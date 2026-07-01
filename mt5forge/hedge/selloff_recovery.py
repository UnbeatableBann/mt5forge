"""Gradual hedge unwind toward no-profit-no-loss."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from mt5forge.positions import Position


class RecoveryAction(StrEnum):
    HOLD = "hold"
    PARTIAL_CLOSE_PROFITABLE_LEG = "partial_close_profitable_leg"
    CLOSE_ALL = "close_all"
    FORCE_REDUCE = "force_reduce"


@dataclass(slots=True, frozen=True)
class HedgePair:
    primary: Position
    hedge: Position

    @property
    def net_pnl(self) -> float:
        return self.primary.profit + self.hedge.profit + self.primary.swap + self.hedge.swap

    @property
    def profitable_ticket(self) -> int:
        return self.primary.ticket if self.primary.profit >= self.hedge.profit else self.hedge.ticket


class SelloffRecovery:
    """Evaluate and unwind hedged pairs while targeting non-negative net P&L."""

    def __init__(self, target_net_pnl: float = 0.0, partial_close_ratio: float = 0.5) -> None:
        self.target_net_pnl = target_net_pnl
        self.partial_close_ratio = partial_close_ratio

    def evaluate(self, pair: HedgePair) -> tuple[RecoveryAction, int | None, float]:
        if pair.net_pnl >= self.target_net_pnl:
            return RecoveryAction.CLOSE_ALL, pair.primary.ticket, pair.net_pnl
        profitable = pair.primary if pair.primary.profit > pair.hedge.profit else pair.hedge
        losing = pair.hedge if profitable is pair.primary else pair.primary
        if profitable.profit > abs(losing.profit) * 0.5:
            lot = max(profitable.lot * self.partial_close_ratio, 0.01)
            return RecoveryAction.PARTIAL_CLOSE_PROFITABLE_LEG, profitable.ticket, lot
        if profitable.lot > losing.lot * 2:
            return RecoveryAction.FORCE_REDUCE, profitable.ticket, profitable.lot - losing.lot
        return RecoveryAction.HOLD, None, pair.net_pnl
