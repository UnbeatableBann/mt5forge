"""Historical data loading."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from mt5forge.core.constants import Timeframe
from mt5forge.core.exceptions import BacktestError


class HistoricalDataLoader:
    """Load and validate OHLCV historical data."""

    REQUIRED_COLUMNS = {"time", "open", "high", "low", "close"}

    def __init__(self, data: pd.DataFrame | None = None, path: str | Path | None = None) -> None:
        self.data = data
        self.path = Path(path) if path else Path()

    @classmethod
    def from_dataframe(cls, data: pd.DataFrame) -> HistoricalDataLoader:
        return cls(data=data)

    def load(
        self,
        symbol: str,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
        path: str | Path | None = None,
    ) -> pd.DataFrame:
        source_path = Path(path) if path else self.path
        if self.data is not None:
            frame = self.data.copy()
        elif source_path:
            if not source_path.exists():
                raise BacktestError(f"Historical data file not found: {source_path}")
            frame = pd.read_csv(source_path)
        else:
            raise BacktestError("HistoricalDataLoader requires a DataFrame or CSV path")
        return self._prepare(frame, start, end)

    def _prepare(self, frame: pd.DataFrame, start: datetime, end: datetime) -> pd.DataFrame:
        missing = self.REQUIRED_COLUMNS - set(frame.columns)
        if missing:
            raise BacktestError(f"Historical data missing columns: {sorted(missing)}")
        frame = frame.copy()
        frame["time"] = pd.to_datetime(frame["time"], utc=True)
        frame = frame.sort_values("time").reset_index(drop=True)
        start_ts = self._utc_timestamp(start)
        end_ts = self._utc_timestamp(end)
        mask = (frame["time"] >= start_ts) & (frame["time"] <= end_ts)
        filtered = frame.loc[mask].reset_index(drop=True)
        if filtered.empty:
            raise BacktestError("Historical replay range contains no rows")
        if filtered[["open", "high", "low", "close"]].isna().any().any():
            raise BacktestError("Historical data contains NaN OHLC values")
        return filtered

    @staticmethod
    def _utc_timestamp(value: datetime) -> pd.Timestamp:
        timestamp = pd.Timestamp(value)
        if timestamp.tzinfo is None:
            return timestamp.tz_localize("UTC")
        return timestamp.tz_convert("UTC")
