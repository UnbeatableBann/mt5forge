"""Portfolio-wide analytics."""

from __future__ import annotations

from dataclasses import dataclass, field

from mt5forge.positions.position_tracker import Position, PositionTracker


@dataclass(slots=True, frozen=True)
class PortfolioSnapshot:
    total_positions: int
    total_lots: float
    unrealized_pnl: float
    exposure_by_symbol: dict[str, float] = field(default_factory=dict)


class PortfolioManager:
    """Aggregate exposure, lots, and floating P&L."""

    def __init__(self, tracker: PositionTracker) -> None:
        self.tracker = tracker

    def snapshot(self) -> PortfolioSnapshot:
        positions = self.tracker.get_all()
        return self.from_positions(positions)

    @staticmethod
    def from_positions(positions: list[Position]) -> PortfolioSnapshot:
        exposure: dict[str, float] = {}
        for position in positions:
            signed = position.lot if position.order_type.is_buy else -position.lot
            exposure[position.symbol] = exposure.get(position.symbol, 0.0) + signed
        return PortfolioSnapshot(
            total_positions=len(positions),
            total_lots=sum(position.lot for position in positions),
            unrealized_pnl=sum(position.profit for position in positions),
            exposure_by_symbol=exposure,
        )
