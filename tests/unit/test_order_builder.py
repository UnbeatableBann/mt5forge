from __future__ import annotations

from mt5forge.core.constants import OrderType
from mt5forge.orders import OrderBuilder, OrderRequest
from tests.mocks.mock_mt5 import MockMT5


def test_order_builder_market_request():
    mt5 = MockMT5()
    builder = OrderBuilder(mt5)
    request = builder.build_market_request(
        OrderRequest("EURUSD", OrderType.BUY, lot=0.1, sl=1.09, tp=1.12, magic=123),
        price=1.1,
    )
    assert request["action"] == mt5.TRADE_ACTION_DEAL
    assert request["type"] == mt5.ORDER_TYPE_BUY
    assert request["volume"] == 0.1
    assert request["magic"] == 123
