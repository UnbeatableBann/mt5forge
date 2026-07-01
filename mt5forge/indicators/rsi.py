"""Relative Strength Index indicator."""

from __future__ import annotations

import numpy as np
import pandas as pd

from mt5forge.indicators.moving_averages import ArrayLike


def RSI(close: ArrayLike, period: int = 14) -> pd.Series | np.ndarray:
    series = close.astype(float) if isinstance(close, pd.Series) else pd.Series(np.asarray(close, dtype=float))
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    result = 100.0 - (100.0 / (1.0 + rs))
    result = result.fillna(100.0).where(avg_loss != 0, 100.0)
    if isinstance(close, np.ndarray):
        return result.to_numpy()
    return result
