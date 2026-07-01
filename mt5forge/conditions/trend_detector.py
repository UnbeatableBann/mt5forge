"""MA-based trend detection."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from mt5forge.conditions.regime import MarketRegime
from mt5forge.indicators import SMA


@dataclass(slots=True, frozen=True)
class TrendSnapshot:
    regime: MarketRegime
    fast_ma: float
    slow_ma: float
    long_ma: float
    slow_slope: float
    strength: float


class TrendDetector:
    """Classify trend using MA(21), MA(50), and MA(200)."""

    def __init__(self, fast: int = 21, slow: int = 50, long: int = 200) -> None:
        self.fast = fast
        self.slow = slow
        self.long = long

    def detect(self, candles: pd.DataFrame) -> TrendSnapshot:
        if len(candles) < self.long + 5:
            return TrendSnapshot(MarketRegime.UNSTABLE, 0.0, 0.0, 0.0, 0.0, 0.0)
        close = candles["close"].astype(float)
        fast_ma = SMA(close, self.fast)
        slow_ma = SMA(close, self.slow)
        long_ma = SMA(close, self.long)
        fast_series = fast_ma if isinstance(fast_ma, pd.Series) else pd.Series(fast_ma)
        slow_series = slow_ma if isinstance(slow_ma, pd.Series) else pd.Series(slow_ma)
        long_series = long_ma if isinstance(long_ma, pd.Series) else pd.Series(long_ma)
        f = float(fast_series.iloc[-1])
        s = float(slow_series.iloc[-1])
        long_ma_val = float(long_series.iloc[-1])
        slope = float(slow_series.iloc[-1] - slow_series.iloc[-5])
        denom = abs(float(close.iloc[-1])) or 1.0
        strength = min(abs(slope) / denom * 10_000.0, 1.0)
        if f > s > long_ma_val and slope > 0:
            regime = MarketRegime.STRONG_BULLISH
        elif f > s and s < long_ma_val:
            regime = MarketRegime.WEAK_BULLISH
        elif f < s < long_ma_val and slope < 0:
            regime = MarketRegime.STRONG_BEARISH
        elif f < s and s > long_ma_val:
            regime = MarketRegime.WEAK_BEARISH
        elif abs(f - s) / denom < 0.0005 and abs(s - long_ma_val) / denom < 0.001:
            regime = MarketRegime.RANGING
        else:
            regime = MarketRegime.SIDEWAYS
        return TrendSnapshot(regime=regime, fast_ma=f, slow_ma=s, long_ma=long_ma_val, slow_slope=slope, strength=strength)
