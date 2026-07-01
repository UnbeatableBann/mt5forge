"""Backtest configuration model."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BacktestConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    spread_pips: float = Field(default=1.5, ge=0.0)
    slippage_pips: float = Field(default=0.5, ge=0.0)
    commission_per_lot: float = Field(default=3.5, ge=0.0)
    initial_balance: float = Field(default=10_000.0, gt=0.0)
    simulate_weekend_gaps: bool = True
    simulate_partial_fills: bool = False
    historical_data_path: str = ""
    random_seed: int = 42
