"""MACD indicator."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from mt5forge.indicators.moving_averages import EMA, ArrayLike


@dataclass(slots=True, frozen=True)
class MACDResult:
    macd_line: pd.Series | np.ndarray
    signal_line: pd.Series | np.ndarray
    histogram: pd.Series | np.ndarray


def MACD(
    close: ArrayLike,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[pd.Series | np.ndarray, pd.Series | np.ndarray, pd.Series | np.ndarray]:
    fast_ema = EMA(close, fast)
    slow_ema = EMA(close, slow)
    if isinstance(fast_ema, np.ndarray):
        macd_line = fast_ema - slow_ema
        signal_line = EMA(macd_line, signal)
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    macd_line = fast_ema - slow_ema
    signal_line = EMA(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram
