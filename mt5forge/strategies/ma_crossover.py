"""Moving Average Crossover strategy."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from mt5forge.core.constants import SignalDirection, Timeframe
from mt5forge.indicators import SMA, CrossoverDetector, CrossoverType
from mt5forge.strategies.base import Signal, StrategyBase, StrategyConfig


@dataclass(slots=True)
class MACrossoverConfig(StrategyConfig):
    fast_ma: int = 21
    slow_ma: int = 50
    trend_ma: int = 200
    use_shift: bool = False
    shift_period: int = 1
    timeframe: Timeframe = Timeframe.H1
    sl_pips: float = 30.0
    tp_pips: float = 60.0
    min_trend_strength: float = 0.6

    def __post_init__(self) -> None:
        self.timeframes = [self.timeframe]


class MACrossoverStrategy(StrategyBase):
    name = "ma_crossover"

    def __init__(self, config: MACrossoverConfig) -> None:
        super().__init__(config)
        self.config: MACrossoverConfig = config
        self.detector = CrossoverDetector()

    def on_candle(self, symbol: str, tf: Timeframe, candles: pd.DataFrame) -> Signal | None:
        required = self.config.trend_ma + self.config.shift_period + 5
        signal: Signal | None = None
        if len(candles) < required:
            return signal
        close = candles["close"].astype(float)
        shift = self.config.shift_period if self.config.use_shift else 0
        fast = SMA(close, self.config.fast_ma, shift=shift)
        slow = SMA(close, self.config.slow_ma, shift=shift)
        trend = SMA(close, self.config.trend_ma, shift=shift)
        event = self.detector.detect(fast, slow)
        if event is None or event.bar_index != len(candles) - 1:
            return signal
        slow_series = slow if isinstance(slow, pd.Series) else pd.Series(slow)
        trend_series = trend if isinstance(trend, pd.Series) else pd.Series(trend)
        slope = float(slow_series.iloc[-1] - slow_series.iloc[-5])
        price = float(close.iloc[-1])
        trend_value = float(trend_series.iloc[-1])
        strength = min(abs(slope) / (abs(price) or 1.0) * 10_000.0, 1.0)
        spread_ok = self._spread_ok(candles)
        if event.type == CrossoverType.BULLISH_CROSS and price > trend_value and slope > 0 and spread_ok and strength >= self.config.min_trend_strength:
            signal = Signal(
                direction=SignalDirection.BUY,
                symbol=symbol,
                strength=strength,
                suggested_sl_pips=self.config.sl_pips,
                suggested_tp_pips=self.config.tp_pips,
                reason="MA fast crossed above slow with long-term uptrend",
            )
        elif event.type == CrossoverType.BEARISH_CROSS and price < trend_value and slope < 0 and spread_ok and strength >= self.config.min_trend_strength:
            signal = Signal(
                direction=SignalDirection.SELL,
                symbol=symbol,
                strength=strength,
                suggested_sl_pips=self.config.sl_pips,
                suggested_tp_pips=self.config.tp_pips,
                reason="MA fast crossed below slow with long-term downtrend",
            )
        return signal

    @staticmethod
    def _spread_ok(candles: pd.DataFrame) -> bool:
        if "spread" not in candles.columns or candles["spread"].dropna().empty:
            return True
        current = float(candles["spread"].iloc[-1])
        average = float(candles["spread"].tail(100).mean())
        return current <= max(average * 2.0, average + 1.0)
