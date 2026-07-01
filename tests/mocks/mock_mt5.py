"""Complete MT5 API mock used by tests."""

from __future__ import annotations

from collections import namedtuple
from dataclasses import dataclass, field
from typing import Any

AccountInfo = namedtuple(
    "AccountInfo",
    "login server balance equity margin margin_free margin_level currency trade_allowed",
)
TerminalInfo = namedtuple("TerminalInfo", "connected build")
SymbolInfo = namedtuple(
    "SymbolInfo",
    "name trade_mode volume_min volume_max volume_step trade_contract_size point digits spread currency_profit currency_margin",
)
TickInfo = namedtuple("TickInfo", "time time_msc bid ask last volume volume_real")
OrderResult = namedtuple("OrderResult", "retcode order deal price volume comment")
PositionInfo = namedtuple(
    "PositionInfo",
    "ticket symbol type volume price_open price_current profit magic swap commission time",
)


@dataclass(slots=True)
class MockMT5:
    initialized: bool = False
    orders: list[dict[str, Any]] = field(default_factory=list)
    positions: list[PositionInfo] = field(default_factory=list)
    next_ticket: int = 1000
    path: str = ""
    account: int = 0
    password: str = ""
    server: str = ""

    TIMEFRAME_H1 = 60
    TRADE_ACTION_DEAL = 1
    TRADE_ACTION_PENDING = 5
    TRADE_ACTION_SLTP = 6
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    ORDER_TYPE_BUY_LIMIT = 2
    ORDER_TYPE_SELL_LIMIT = 3
    ORDER_TYPE_BUY_STOP = 4
    ORDER_TYPE_SELL_STOP = 5
    ORDER_TYPE_BUY_STOP_LIMIT = 6
    ORDER_TYPE_SELL_STOP_LIMIT = 7
    ORDER_TIME_GTC = 0
    ORDER_FILLING_IOC = 1
    ORDER_FILLING_RETURN = 2
    TRADE_RETCODE_DONE = 10009
    TRADE_RETCODE_PLACED = 10008

    def initialize(self, path: str = "") -> bool:
        self.initialized = True
        self.path = path
        return True

    def login(self, account: int, password: str, server: str) -> bool:
        self.account = account
        self.password = password
        self.server = server
        return bool(account and password and server)

    def shutdown(self) -> None:
        self.initialized = False

    def last_error(self) -> tuple[int, str]:
        return (0, "ok")

    def terminal_info(self) -> TerminalInfo | bool:
        return TerminalInfo(True, 4200) if self.initialized else False

    def account_info(self) -> AccountInfo:
        return AccountInfo(123456, "Demo", 10_000.0, 10_000.0, 0.0, 10_000.0, 500.0, "USD", True)

    def symbol_info(self, symbol: str) -> SymbolInfo:
        return SymbolInfo(symbol, 1, 0.01, 10.0, 0.01, 100_000.0, 0.00001, 5, 10.0, "USD", "USD")

    def symbol_info_tick(self, symbol: str) -> TickInfo:
        return TickInfo(1_700_000_000, 1_700_000_000_000, 1.1000, 1.1002, 1.1001, 1.0, 1.0)

    def order_send(self, request: dict[str, Any]) -> OrderResult:
        self.orders.append(request)
        ticket = self.next_ticket
        self.next_ticket += 1
        if request.get("action") == self.TRADE_ACTION_DEAL and "position" not in request:
            self.positions.append(
                PositionInfo(
                    ticket,
                    request["symbol"],
                    request["type"],
                    request["volume"],
                    request["price"],
                    request["price"],
                    0.0,
                    request.get("magic", 0),
                    0.0,
                    0.0,
                    1_700_000_000,
                )
            )
        return OrderResult(self.TRADE_RETCODE_DONE, ticket, ticket, request.get("price", 0.0), request.get("volume", 0.0), "done")

    def positions_get(self, ticket: int | None = None, symbol: str | None = None):
        positions = self.positions
        if ticket is not None:
            positions = [position for position in positions if position.ticket == ticket]
        if symbol is not None:
            positions = [position for position in positions if position.symbol == symbol]
        return positions

    def copy_rates_from_pos(self, symbol: str, timeframe: int, shift: int, count: int):
        import numpy as np

        dtype = [
            ("time", "i8"),
            ("open", "f8"),
            ("high", "f8"),
            ("low", "f8"),
            ("close", "f8"),
            ("tick_volume", "i8"),
            ("spread", "i8"),
            ("real_volume", "i8"),
        ]
        rows = []
        for idx in range(count):
            price = 1.1000 + idx * 0.0001
            rows.append((1_700_000_000 + (shift + idx) * 3600, price, price + 0.0005, price - 0.0005, price + 0.0002, 100, 10, 100))
        return np.array(rows, dtype=dtype)
