"""Hedge escalation guard."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class HedgeLayer:
    symbol: str
    primary_ticket: int
    hedge_ticket: int
    lot: float


class HedgeGuard:
    """Prevent hedge escalation spirals with layer and exposure caps."""

    def __init__(self, max_layers: int = 3, max_exposure_lots: float = 3.0) -> None:
        self.max_layers = max_layers
        self.max_exposure_lots = max_exposure_lots
        self.layers: list[HedgeLayer] = []

    def can_open(self, symbol: str, lot: float) -> bool:
        symbol_layers = [layer for layer in self.layers if layer.symbol == symbol]
        projected_exposure = self.total_exposure(symbol) + lot
        return len(symbol_layers) < self.max_layers and projected_exposure <= self.max_exposure_lots

    def record_layer(self, layer: HedgeLayer) -> None:
        if self.can_open(layer.symbol, layer.lot):
            self.layers.append(layer)

    def total_exposure(self, symbol: str | None = None) -> float:
        layers = self.layers if symbol is None else [layer for layer in self.layers if layer.symbol == symbol]
        return sum(layer.lot for layer in layers)

    def should_force_stop(self, symbol: str) -> bool:
        symbol_layers = [layer for layer in self.layers if layer.symbol == symbol]
        return len(symbol_layers) >= self.max_layers or self.total_exposure(symbol) >= self.max_exposure_lots

    def remove_by_ticket(self, ticket: int) -> None:
        self.layers = [layer for layer in self.layers if layer.primary_ticket != ticket and layer.hedge_ticket != ticket]
