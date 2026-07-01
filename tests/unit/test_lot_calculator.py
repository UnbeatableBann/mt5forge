from __future__ import annotations

from mt5forge.config import RiskConfig
from mt5forge.risk import LotCalculator


def test_lot_calculator_percentage_and_fixed():
    config = RiskConfig(risk_per_trade_pct=1.0, min_lot_size=0.01, max_lot_size=2.0)
    calc = LotCalculator(config)
    assert calc.percentage_risk(10_000, 50, "EURUSD") == 0.2

    fixed = LotCalculator(config.model_copy(update={"use_fixed_lot": True, "fixed_lot_size": 0.3}))
    assert fixed.calculate(10_000, 50, "EURUSD") == 0.3
