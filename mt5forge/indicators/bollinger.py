"""Bollinger Bands indicator."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from mt5forge.indicators.moving_averages import SMA, ArrayLike


@dataclass(slots=True, frozen=True)
class BollingerResult:
    upper: pd.Series | np.ndarray
    middle: pd.Series | np.ndarray
    lower: pd.Series | np.ndarray
    bandwidth: pd.Series | np.ndarray


def BollingerBands(close: ArrayLike, period: int = 20, std_dev: float = 2.0) -> BollingerResult:
    series = close.astype(float) if isinstance(close, pd.Series) else pd.Series(np.asarray(close, dtype=float))
    middle = SMA(close, period)
    rolling_std = series.rolling(period, min_periods=period).std(ddof=0)
    mid_series = pd.Series(middle) if isinstance(middle, np.ndarray) else middle
    upper = mid_series + rolling_std * std_dev
    lower = mid_series - rolling_std * std_dev
    bandwidth = (upper - lower) / mid_series.replace(0.0, np.nan)
    if isinstance(close, np.ndarray):
        return BollingerResult(
            upper=upper.to_numpy(),
            middle=mid_series.to_numpy(),
            lower=lower.to_numpy(),
            bandwidth=bandwidth.to_numpy(),
        )
    return BollingerResult(upper=upper, middle=mid_series, lower=lower, bandwidth=bandwidth)
