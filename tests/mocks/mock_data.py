"""Sample market data fixtures."""

from __future__ import annotations

import pandas as pd


def sample_candles(rows: int = 260) -> pd.DataFrame:
    times = pd.date_range("2024-01-01", periods=rows, freq="h", tz="UTC")
    close = pd.Series([1.1000 + idx * 0.00015 for idx in range(rows)])
    frame = pd.DataFrame(
        {
            "time": times,
            "open": close - 0.00005,
            "high": close + 0.0004,
            "low": close - 0.0004,
            "close": close,
            "tick_volume": 100,
            "spread": 10,
            "real_volume": 100,
        }
    )
    return frame
