"""Dynamic lot sizing."""

from __future__ import annotations

import math

from mt5forge.config.risk_config import RiskConfig
from mt5forge.core.constants import DEFAULT_PIP_SIZE, JPY_PIP_SIZE


class LotCalculator:
    """Implement percentage, fractional, fixed, and volatility-adjusted sizing."""

    def __init__(self, config: RiskConfig) -> None:
        self.config = config

    def calculate(
        self,
        balance: float,
        sl_pips: float,
        symbol: str,
        pip_value_per_lot: float | None = None,
        strength: float = 1.0,
    ) -> float:
        if self.config.use_fixed_lot:
            return self._normalize(self.config.fixed_lot_size)
        lot = self.percentage_risk(balance, sl_pips, symbol, pip_value_per_lot) * max(min(strength, 1.0), 0.0)
        return self._normalize(lot)

    def percentage_risk(
        self,
        balance: float,
        sl_pips: float,
        symbol: str,
        pip_value_per_lot: float | None = None,
    ) -> float:
        if sl_pips <= 0:
            raise ValueError("sl_pips must be positive for percentage risk sizing")
        risk_amount = balance * (self.config.risk_per_trade_pct / 100.0)
        pip_value = pip_value_per_lot or self._default_pip_value(symbol)
        return risk_amount / (sl_pips * pip_value)

    def fixed_fractional(self, balance: float, fraction: float, contract_size: float = 100_000.0) -> float:
        if fraction <= 0 or contract_size <= 0:
            raise ValueError("fraction and contract_size must be positive")
        return self._normalize(balance * fraction / contract_size)

    def fixed_lot(self) -> float:
        return self._normalize(self.config.fixed_lot_size)

    def volatility_adjusted(self, base_lot: float, target_atr: float, current_atr: float) -> float:
        if current_atr <= 0:
            raise ValueError("current_atr must be positive")
        return self._normalize(base_lot * (target_atr / current_atr))

    def _normalize(self, lot: float) -> float:
        bounded = min(max(lot, self.config.min_lot_size), self.config.max_lot_size)
        step = self.config.min_lot_size
        normalized = math.floor(bounded / step) * step
        return round(max(normalized, self.config.min_lot_size), 8)

    @staticmethod
    def _default_pip_value(symbol: str) -> float:
        pip_size = JPY_PIP_SIZE if symbol.upper().endswith("JPY") else DEFAULT_PIP_SIZE
        return 100_000.0 * pip_size
