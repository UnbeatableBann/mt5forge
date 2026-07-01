"""Average True Range indicator."""

from __future__ import annotations

import numpy as np
import pandas as pd

from mt5forge.indicators.moving_averages import ArrayLike


def ATR(high: ArrayLike, low: ArrayLike, close: ArrayLike, period: int = 14) -> pd.Series | np.ndarray:
    high_s = _series(high)
    low_s = _series(low)
    close_s = _series(close)
    previous_close = close_s.shift(1)
    true_range = pd.concat(
        [
            (high_s - low_s).abs(),
            (high_s - previous_close).abs(),
            (low_s - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    result = true_range.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    if isinstance(high, np.ndarray):
        return result.to_numpy()
    return result


def _series(data: ArrayLike) -> pd.Series:
    if isinstance(data, pd.Series):
        return data.astype(float)
    return pd.Series(np.asarray(data, dtype=float))
