"""Crossover detection utility."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

import numpy as np
import pandas as pd

from mt5forge.indicators.moving_averages import ArrayLike


class CrossoverType(StrEnum):
    BULLISH_CROSS = "bullish_cross"
    BEARISH_CROSS = "bearish_cross"


@dataclass(slots=True, frozen=True)
class CrossoverEvent:
    type: CrossoverType
    bar_index: int
    fast_value: float
    slow_value: float


class CrossoverDetector:
    """Detect the most recent bullish or bearish series cross."""

    def detect(self, fast: ArrayLike, slow: ArrayLike) -> CrossoverEvent | None:
        fast_s = fast.astype(float) if isinstance(fast, pd.Series) else pd.Series(np.asarray(fast, dtype=float))
        slow_s = slow.astype(float) if isinstance(slow, pd.Series) else pd.Series(np.asarray(slow, dtype=float))
        event: CrossoverEvent | None = None
        limit = min(len(fast_s), len(slow_s))
        for idx in range(1, limit):
            prev_fast = float(fast_s.iloc[idx - 1])
            prev_slow = float(slow_s.iloc[idx - 1])
            current_fast = float(fast_s.iloc[idx])
            current_slow = float(slow_s.iloc[idx])
            if np.isnan([prev_fast, prev_slow, current_fast, current_slow]).any():
                continue
            if prev_fast <= prev_slow and current_fast > current_slow:
                event = CrossoverEvent(CrossoverType.BULLISH_CROSS, idx, current_fast, current_slow)
            elif prev_fast >= prev_slow and current_fast < current_slow:
                event = CrossoverEvent(CrossoverType.BEARISH_CROSS, idx, current_fast, current_slow)
        return event
