"""Risk configuration model."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RiskConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    risk_per_trade_pct: float = Field(default=1.0, ge=0.0, le=100.0)
    max_daily_loss_pct: float = Field(default=5.0, ge=0.0, le=100.0)
    max_drawdown_pct: float = Field(default=15.0, ge=0.0, le=100.0)
    max_concurrent_trades: int = Field(default=10, ge=1)
    max_lot_size: float = Field(default=1.0, gt=0.0)
    min_lot_size: float = Field(default=0.01, gt=0.0)
    max_exposure_per_symbol: float = Field(default=2.0, gt=0.0)
    margin_level_minimum: float = Field(default=150.0, ge=0.0)
    consecutive_loss_limit: int = Field(default=5, ge=1)
    cooldown_after_loss_seconds: int = Field(default=300, ge=0)
    max_hedge_exposure_lots: float = Field(default=3.0, gt=0.0)
    use_fixed_lot: bool = False
    fixed_lot_size: float = Field(default=0.1, gt=0.0)

    @model_validator(mode="after")
    def validate_lot_bounds(self) -> RiskConfig:
        if self.min_lot_size > self.max_lot_size:
            raise ValueError("min_lot_size must be less than or equal to max_lot_size")
        if self.use_fixed_lot and not self.min_lot_size <= self.fixed_lot_size <= self.max_lot_size:
            raise ValueError("fixed_lot_size must be within configured lot bounds")
        return self
