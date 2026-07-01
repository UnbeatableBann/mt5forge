"""P&L and reward:risk calculations."""

from __future__ import annotations

from mt5forge.core.constants import DEFAULT_PIP_SIZE, JPY_PIP_SIZE


class PnLCalculator:
    """Currency, pip, and reward:risk utilities."""

    @staticmethod
    def pip_size(symbol: str) -> float:
        return JPY_PIP_SIZE if symbol.upper().endswith("JPY") else DEFAULT_PIP_SIZE

    def calculate_rr_ratio(self, entry: float, sl: float, tp: float, direction: str) -> float:
        normalized = direction.upper()
        if normalized == "BUY":
            risk = entry - sl
            reward = tp - entry
        else:
            risk = sl - entry
            reward = entry - tp
        if risk <= 0:
            raise ValueError("Stop loss must define positive risk")
        return reward / risk

    def calculate_pnl_pips(self, entry: float, current: float, direction: str, symbol: str) -> float:
        size = self.pip_size(symbol)
        raw = (current - entry) / size
        return raw if direction.upper() == "BUY" else -raw

    def calculate_pnl_currency(self, pips: float, lot: float, symbol: str) -> float:
        pip_value = 100_000.0 * self.pip_size(symbol)
        return pips * lot * pip_value
