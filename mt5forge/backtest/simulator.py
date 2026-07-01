"""Simulated broker for historical replay."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from mt5forge.backtest.slippage_sim import SlippageSimulator
from mt5forge.backtest.spread_sim import SpreadSimulator
from mt5forge.core.constants import OrderType
from mt5forge.orders import OrderRequest
from mt5forge.positions import PnLCalculator


@dataclass(slots=True)
class SimulatedPosition:
    ticket: int
    symbol: str
    order_type: OrderType
    lot: float
    entry_price: float
    sl: float | None
    tp: float | None
    opened_at: datetime


@dataclass(slots=True)
class SimulatedTrade:
    ticket: int
    symbol: str
    order_type: OrderType
    lot: float
    entry_price: float
    exit_price: float
    profit: float
    opened_at: datetime
    closed_at: datetime


class SimulatedBroker:
    """Replicate live execution with spread, slippage, and commission."""

    def __init__(
        self,
        initial_balance: float,
        spread_simulator: SpreadSimulator,
        slippage_simulator: SlippageSimulator,
        commission_per_lot: float = 3.5,
    ) -> None:
        self.balance = initial_balance
        self.equity = initial_balance
        self.spread_simulator = spread_simulator
        self.slippage_simulator = slippage_simulator
        self.commission_per_lot = commission_per_lot
        self.positions: dict[int, SimulatedPosition] = {}
        self.trades: list[SimulatedTrade] = []
        self.equity_curve: list[tuple[datetime, float]] = []
        self._ticket = 1
        self.pnl = PnLCalculator()

    def place_market_order(self, request: OrderRequest, candle: pd.Series) -> SimulatedPosition:
        pip = self.pnl.pip_size(request.symbol)
        spread = self.spread_simulator.spread(candle) * pip
        slippage = self.slippage_simulator.slippage() * pip
        base = float(candle["open"])
        price = base + spread / 2.0 + slippage if request.order_type.is_buy else base - spread / 2.0 - slippage
        position = SimulatedPosition(
            ticket=self._ticket,
            symbol=request.symbol,
            order_type=request.order_type,
            lot=request.lot,
            entry_price=price,
            sl=request.sl,
            tp=request.tp,
            opened_at=pd.Timestamp(candle["time"]).to_pydatetime(),
        )
        self.positions[position.ticket] = position
        self._ticket += 1
        return position

    def process_candle(self, candle: pd.Series) -> list[SimulatedTrade]:
        closed: list[SimulatedTrade] = []
        high = float(candle["high"])
        low = float(candle["low"])
        close = float(candle["close"])
        closed_at = pd.Timestamp(candle["time"]).to_pydatetime()
        for ticket, position in list(self.positions.items()):
            exit_price = close
            should_close = False
            if position.order_type.is_buy:
                if position.sl is not None and low <= position.sl:
                    exit_price = position.sl
                    should_close = True
                elif position.tp is not None and high >= position.tp:
                    exit_price = position.tp
                    should_close = True
            else:
                if position.sl is not None and high >= position.sl:
                    exit_price = position.sl
                    should_close = True
                elif position.tp is not None and low <= position.tp:
                    exit_price = position.tp
                    should_close = True
            if should_close:
                closed.append(self.close_position(ticket, exit_price, closed_at))
        self._mark_to_market(close, closed_at)
        return closed

    def close_position(self, ticket: int, price: float, closed_at: datetime) -> SimulatedTrade:
        position = self.positions.pop(ticket)
        direction = "BUY" if position.order_type.is_buy else "SELL"
        pips = self.pnl.calculate_pnl_pips(position.entry_price, price, direction, position.symbol)
        profit = self.pnl.calculate_pnl_currency(pips, position.lot, position.symbol) - self.commission_per_lot * position.lot
        self.balance += profit
        trade = SimulatedTrade(
            ticket=ticket,
            symbol=position.symbol,
            order_type=position.order_type,
            lot=position.lot,
            entry_price=position.entry_price,
            exit_price=price,
            profit=profit,
            opened_at=position.opened_at,
            closed_at=closed_at,
        )
        self.trades.append(trade)
        self._mark_to_market(price, closed_at)
        return trade

    def close_all(self, price: float, closed_at: datetime) -> list[SimulatedTrade]:
        return [self.close_position(ticket, price, closed_at) for ticket in list(self.positions)]

    def _mark_to_market(self, price: float, timestamp: datetime) -> None:
        floating = 0.0
        for position in self.positions.values():
            direction = "BUY" if position.order_type.is_buy else "SELL"
            pips = self.pnl.calculate_pnl_pips(position.entry_price, price, direction, position.symbol)
            floating += self.pnl.calculate_pnl_currency(pips, position.lot, position.symbol)
        self.equity = self.balance + floating
        self.equity_curve.append((timestamp, self.equity))
