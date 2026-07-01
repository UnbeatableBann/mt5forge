"""Live position state tracking."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from mt5forge.connection.connector import MT5Connector
from mt5forge.core.constants import OrderType


@dataclass(slots=True, frozen=True)
class Position:
    ticket: int
    symbol: str
    order_type: OrderType
    lot: float
    entry_price: float
    current_price: float
    profit: float
    magic: int = 0
    swap: float = 0.0
    commission: float = 0.0
    time: datetime = datetime.now(UTC)

    @classmethod
    def from_mt5(cls, raw: Any) -> Position:
        data = raw._asdict() if hasattr(raw, "_asdict") else dict(raw)
        raw_type = int(data.get("type", 0))
        order_type = OrderType.BUY if raw_type == 0 else OrderType.SELL
        timestamp = float(data.get("time", 0.0))
        return cls(
            ticket=int(data.get("ticket", 0)),
            symbol=str(data.get("symbol", "")),
            order_type=order_type,
            lot=float(data.get("volume", 0.0)),
            entry_price=float(data.get("price_open", 0.0)),
            current_price=float(data.get("price_current", data.get("price_open", 0.0))),
            profit=float(data.get("profit", 0.0)),
            magic=int(data.get("magic", 0)),
            swap=float(data.get("swap", 0.0)),
            commission=float(data.get("commission", 0.0)),
            time=datetime.fromtimestamp(timestamp, tz=UTC) if timestamp else datetime.now(UTC),
        )


class PositionTracker:
    """Read and cache live MT5 positions."""

    def __init__(self, connector: MT5Connector | None = None) -> None:
        self.connector = connector
        self._positions: dict[int, Position] = {}

    def update(self) -> list[Position]:
        if self.connector is None:
            return list(self._positions.values())
        raw_positions = self.connector.mt5.positions_get() or []
        self._positions = {Position.from_mt5(raw).ticket: Position.from_mt5(raw) for raw in raw_positions}
        return list(self._positions.values())

    def set_positions(self, positions: list[Position]) -> None:
        self._positions = {position.ticket: position for position in positions}

    def get_all(self) -> list[Position]:
        return self.update() if self.connector is not None else list(self._positions.values())

    def get_by_ticket(self, ticket: int) -> Position | None:
        positions = self.get_all()
        match = next((position for position in positions if position.ticket == ticket), None)
        return match

    def by_symbol(self, symbol: str) -> list[Position]:
        return [position for position in self.get_all() if position.symbol == symbol]
