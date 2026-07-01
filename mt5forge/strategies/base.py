"""Strategy base classes and signal models."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import pandas as pd

from mt5forge.conditions import MarketRegime
from mt5forge.core.constants import SignalDirection, Timeframe
from mt5forge.market import Tick
from mt5forge.positions import Position


@dataclass(slots=True)
class StrategyConfig:
    enabled: bool = True
    symbols: list[str] = field(default_factory=lambda: ["EURUSD"])
    timeframes: list[Timeframe] = field(default_factory=lambda: [Timeframe.H1])
    magic: int = 10001
    lot: float = 0.1
    risk_multiplier: float = 1.0


@dataclass(slots=True)
class Signal:
    direction: SignalDirection
    symbol: str
    strength: float = 1.0
    suggested_sl_pips: float | None = None
    suggested_tp_pips: float | None = None
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True, frozen=True)
class TradeResult:
    ticket: int
    symbol: str
    profit: float
    closed_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class StrategyBase(ABC):
    """Base class for all strategies. Strategies emit signals and never call MT5."""

    name = "strategy"
    magic = 10001
    symbols: list[str] = ["EURUSD"]
    timeframes: list[Timeframe] = [Timeframe.H1]

    def __init__(self, config: StrategyConfig) -> None:
        self.config = config
        self.symbols = list(config.symbols)
        self.timeframes = list(config.timeframes)
        self.magic = config.magic
        self._positions_provider: Callable[[], list[Position]] = list
        self._balance_provider: Callable[[], float] = float
        self._condition_provider: Callable[[], MarketRegime] = lambda: MarketRegime.UNSTABLE

    @abstractmethod
    def on_candle(self, symbol: str, tf: Timeframe, candles: pd.DataFrame) -> Signal | None:
        signal: Signal | None = Signal(direction=SignalDirection.HOLD, symbol=symbol, reason="base_strategy")
        return signal

    def on_tick(self, symbol: str, tick: Tick) -> Signal | None:
        signal: Signal | None = None
        return signal

    def on_trade_closed(self, result: TradeResult) -> None:
        self._last_trade_result = result

    def on_market_condition_change(self, condition: MarketRegime) -> None:
        self._last_market_condition = condition

    def bind_context(
        self,
        positions_provider: Callable[[], list[Position]],
        balance_provider: Callable[[], float],
        condition_provider: Callable[[], MarketRegime],
    ) -> None:
        self._positions_provider = positions_provider
        self._balance_provider = balance_provider
        self._condition_provider = condition_provider

    def get_open_positions(self) -> list[Position]:
        return self._positions_provider()

    def get_balance(self) -> float:
        return self._balance_provider()

    def get_market_condition(self) -> MarketRegime:
        return self._condition_provider()
