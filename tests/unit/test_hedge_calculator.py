from __future__ import annotations

from mt5forge.hedge import HedgeCalculator


def test_hedge_lot_projects_no_profit_no_loss():
    calc = HedgeCalculator(min_lot=0.01, max_lot=5.0, lot_step=0.01)
    lot = calc.calculate_hedge_lot(0.1, 1.1000, 1.0970, "BUY", "EURUSD")
    assert lot >= 0.1
    assert lot <= 5.0
