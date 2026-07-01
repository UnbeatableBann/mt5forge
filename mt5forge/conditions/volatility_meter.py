"""ATR-based volatility meter."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from mt5forge.indicators import ATR


@dataclass(slots=True, frozen=True)
class VolatilitySnapshot:
    atr: float
    atr_average: float
    ratio: float
    high_volatility: bool
    low_volatility: bool


class VolatilityMeter:
    """Measure current ATR relative to recent ATR average."""

    def __init__(self, period: int = 14, high_multiplier: float = 2.0, low_multiplier: float = 0.5) -> None:
        self.period = period
        self.high_multiplier = high_multiplier
        self.low_multiplier = low_multiplier

    def measure(self, candles: pd.DataFrame) -> VolatilitySnapshot:
        if len(candles) < self.period * 3:
            return VolatilitySnapshot(0.0, 0.0, 0.0, False, False)
        atr = ATR(candles["high"], candles["low"], candles["close"], self.period)
        atr_series = atr if isinstance(atr, pd.Series) else pd.Series(atr)
        current = float(atr_series.iloc[-1])
        average = float(atr_series.tail(20).mean())
        ratio = current / average if average > 0 else 0.0
        return VolatilitySnapshot(
            atr=current,
            atr_average=average,
            ratio=ratio,
            high_volatility=ratio > self.high_multiplier,
            low_volatility=0 < ratio < self.low_multiplier,
        )
