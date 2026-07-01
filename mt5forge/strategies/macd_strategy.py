"""MACD strategy."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from mt5forge.core.constants import SignalDirection, Timeframe
from mt5forge.indicators import MACD, SMA, CrossoverDetector, CrossoverType
from mt5forge.strategies.base import Signal, StrategyBase, StrategyConfig


@dataclass(slots=True)
class MACDStrategyConfig(StrategyConfig):
    fast_period: int = 12
    slow_period: int = 26
    signal_period: int = 9
    use_histogram_confirmation: bool = True
    min_histogram_threshold: float = 0.0001
    trend_filter_ma: int = 200
    sl_pips: float = 25.0
    rr_ratio: float = 2.0


class MACDStrategy(StrategyBase):
    name = "macd"

    def __init__(self, config: MACDStrategyConfig) -> None:
        super().__init__(config)
        self.config: MACDStrategyConfig = config
        self.detector = CrossoverDetector()

    def on_candle(self, symbol: str, tf: Timeframe, candles: pd.DataFrame) -> Signal | None:
        signal: Signal | None = None
        if len(candles) < self.config.trend_filter_ma + self.config.slow_period:
            return signal
        close = candles["close"].astype(float)
        macd_line, signal_line, histogram = MACD(
            close,
            fast=self.config.fast_period,
            slow=self.config.slow_period,
            signal=self.config.signal_period,
        )
        trend = SMA(close, self.config.trend_filter_ma)
        event = self.detector.detect(macd_line, signal_line)
        if event is None or event.bar_index != len(candles) - 1:
            return signal
        price = float(close.iloc[-1])
        trend_series = trend if isinstance(trend, pd.Series) else pd.Series(trend)
        trend_value = float(trend_series.iloc[-1])
        histogram_series = histogram if isinstance(histogram, pd.Series) else pd.Series(histogram)
        hist = float(histogram_series.iloc[-1])
        threshold_ok = abs(hist) >= self.config.min_histogram_threshold
        if self.config.use_histogram_confirmation and not threshold_ok:
            return signal
        if event.type == CrossoverType.BULLISH_CROSS and hist > 0 and price > trend_value:
            signal = Signal(
                direction=SignalDirection.BUY,
                symbol=symbol,
                suggested_sl_pips=self.config.sl_pips,
                suggested_tp_pips=self.config.sl_pips * self.config.rr_ratio,
                reason="MACD crossed above signal with positive histogram and trend filter",
            )
        elif event.type == CrossoverType.BEARISH_CROSS and hist < 0 and price < trend_value:
            signal = Signal(
                direction=SignalDirection.SELL,
                symbol=symbol,
                suggested_sl_pips=self.config.sl_pips,
                suggested_tp_pips=self.config.sl_pips * self.config.rr_ratio,
                reason="MACD crossed below signal with negative histogram and trend filter",
            )
        return signal
