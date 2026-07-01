"""Indicator base class."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class IndicatorBase(ABC):
    """Base class for custom indicator objects."""

    @abstractmethod
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        return pd.Series(dtype="float64")
