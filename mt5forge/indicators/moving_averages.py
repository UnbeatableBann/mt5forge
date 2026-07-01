"""Moving average indicators."""

from __future__ import annotations

from typing import TypeAlias

import numpy as np
import pandas as pd

ArrayLike: TypeAlias = pd.Series | np.ndarray | list[float]


def SMA(data: ArrayLike, period: int, shift: int = 0) -> pd.Series | np.ndarray:
    series = _series(data)
    result = series.rolling(window=period, min_periods=period).mean()
    if shift:
        result = result.shift(shift)
    return _restore(result, data)


def EMA(data: ArrayLike, period: int, shift: int = 0) -> pd.Series | np.ndarray:
    series = _series(data)
    result = series.ewm(span=period, adjust=False, min_periods=period).mean()
    if shift:
        result = result.shift(shift)
    return _restore(result, data)


def WMA(data: ArrayLike, period: int, shift: int = 0) -> pd.Series | np.ndarray:
    series = _series(data)
    weights = np.arange(1, period + 1, dtype=float)
    result = series.rolling(period, min_periods=period).apply(
        lambda values: float(np.dot(values, weights) / weights.sum()),
        raw=True,
    )
    if shift:
        result = result.shift(shift)
    return _restore(result, data)


def _series(data: ArrayLike) -> pd.Series:
    if isinstance(data, pd.Series):
        return data.astype(float)
    return pd.Series(np.asarray(data, dtype=float))


def _restore(result: pd.Series, template: ArrayLike) -> pd.Series | np.ndarray:
    if isinstance(template, np.ndarray):
        return result.to_numpy()
    return result
