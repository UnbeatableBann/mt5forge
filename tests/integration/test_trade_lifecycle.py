from __future__ import annotations

from mt5forge.config import RiskConfig
from mt5forge.connection import MT5Connector
from mt5forge.core.constants import OrderType, TradeState
from mt5forge.orders import OrderManager, OrderRequest, OrderValidator
from mt5forge.risk import RiskManager
from mt5forge.trade import TradeLifecycle


class AlwaysOpen:
    def is_open(self, symbol):
        return True


def test_trade_lifecycle_places_and_registers(mock_mt5):
    connector = MT5Connector(mt5=mock_mt5)
    connector.initialize()
    risk = RiskManager(RiskConfig())
    validator = OrderValidator(market_hours=AlwaysOpen())
    manager = OrderManager(connector, risk, validator=validator)
    lifecycle = TradeLifecycle(manager)
    result = lifecycle.place(OrderRequest("EURUSD", OrderType.BUY, lot=0.1))
    assert result.success
    assert result.ticket is not None
    record = lifecycle.get(result.ticket)
    assert record is not None
    assert record.state == TradeState.PLACED
