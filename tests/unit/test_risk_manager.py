from __future__ import annotations

from mt5forge.config import RiskConfig
from mt5forge.core.constants import OrderType
from mt5forge.orders import OrderRequest
from mt5forge.risk import RiskManager


def test_risk_manager_rejects_lot_and_margin():
    manager = RiskManager(RiskConfig(max_lot_size=1.0, margin_level_minimum=150.0))
    decision = manager.validate_order(
        OrderRequest("EURUSD", OrderType.BUY, lot=2.0),
        account_info={"balance": 10_000, "equity": 10_000, "margin_level": 100.0},
        positions=[],
    )
    assert not decision.approved
    assert "above_max_lot_size" in decision.reasons
    assert "margin_level_below_minimum" in decision.reasons


def test_risk_manager_records_cooldown():
    manager = RiskManager(RiskConfig(consecutive_loss_limit=2, cooldown_after_loss_seconds=60))
    manager.record_trade_close(-10.0)
    manager.record_trade_close(-5.0)
    decision = manager.validate_order(
        OrderRequest("EURUSD", OrderType.BUY, lot=0.1),
        account_info={"balance": 10_000, "equity": 10_000, "margin_level": 500.0},
        positions=[],
    )
    assert not decision.approved
    assert "trade_cooldown_active" in decision.reasons
