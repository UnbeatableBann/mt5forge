"""Spread simulation."""

from __future__ import annotations


class SpreadSimulator:
    """Apply fixed or candle-provided spread in pips."""

    def __init__(self, spread_pips: float = 1.5) -> None:
        self.spread_pips = spread_pips

    def spread(self, candle: dict[str, float]) -> float:
        if "spread" in candle and float(candle["spread"]) > 0:
            return float(candle["spread"])
        return self.spread_pips
