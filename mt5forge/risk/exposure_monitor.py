"""Exposure limit checks."""

from __future__ import annotations

from typing import Any

from mt5forge.config.risk_config import RiskConfig
from mt5forge.core.constants import OrderType


class ExposureMonitor:
    """Validate per-symbol, portfolio, and hedge exposure limits."""

    def __init__(self, config: RiskConfig) -> None:
        self.config = config

    def exposure_by_symbol(self, positions: list[Any]) -> dict[str, float]:
        exposure: dict[str, float] = {}
        for position in positions:
            data = position._asdict() if hasattr(position, "_asdict") else getattr(position, "__dict__", position)
            symbol = str(data.get("symbol", ""))
            volume = float(data.get("volume", data.get("lot", 0.0)))
            raw_type = data.get("type", data.get("order_type", OrderType.BUY))
            is_buy = raw_type == 0 or raw_type == OrderType.BUY or str(raw_type).upper().endswith("BUY")
            signed = volume if is_buy else -volume
            exposure[symbol] = exposure.get(symbol, 0.0) + signed
        return exposure

    def validate(
        self,
        symbol: str,
        order_type: OrderType,
        lot: float,
        positions: list[Any],
        is_hedge: bool = False,
    ) -> list[str]:
        reasons: list[str] = []
        if len(positions) >= self.config.max_concurrent_trades:
            reasons.append("max_concurrent_trades")
        exposure = self.exposure_by_symbol(positions)
        delta = lot if order_type.is_buy else -lot
        projected = abs(exposure.get(symbol, 0.0) + delta)
        if projected > self.config.max_exposure_per_symbol:
            reasons.append("max_exposure_per_symbol")
        if is_hedge:
            hedge_exposure = sum(abs(value) for value in exposure.values()) + lot
            if hedge_exposure > self.config.max_hedge_exposure_lots:
                reasons.append("max_hedge_exposure_lots")
        return reasons
