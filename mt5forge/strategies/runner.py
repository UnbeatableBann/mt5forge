"""Multi-strategy executor."""

from __future__ import annotations

import threading
from collections import defaultdict

import pandas as pd

from mt5forge.conditions import MarketRegime
from mt5forge.core.constants import ConflictPolicy, OrderType, SignalDirection, StrategyStatus, Timeframe
from mt5forge.core.events import EventBus
from mt5forge.core.exceptions import StrategyError
from mt5forge.orders import OrderManager, OrderRequest
from mt5forge.positions import PositionTracker
from mt5forge.risk import RiskManager
from mt5forge.strategies.base import Signal, StrategyBase


class StrategyRunner:
    """Register, start, pause, stop, and dispatch strategy signals."""

    def __init__(
        self,
        order_manager: OrderManager | None = None,
        risk_manager: RiskManager | None = None,
        position_provider: PositionTracker | None = None,
        event_bus: EventBus | None = None,
        conflict_policy: str | ConflictPolicy = ConflictPolicy.ALLOW_BOTH,
    ) -> None:
        self.order_manager = order_manager
        self.risk_manager = risk_manager
        self.position_provider = position_provider or PositionTracker()
        self.event_bus = event_bus or EventBus()
        self.conflict_policy = ConflictPolicy[conflict_policy] if isinstance(conflict_policy, str) and conflict_policy in ConflictPolicy.__members__ else ConflictPolicy(conflict_policy)
        self._strategies: dict[str, StrategyBase] = {}
        self._status: dict[str, StrategyStatus] = {}
        self._last_signal: dict[str, Signal] = {}
        self._errors: dict[str, list[Exception]] = defaultdict(list)
        self._lock = threading.RLock()

    def register(self, strategy: StrategyBase) -> None:
        with self._lock:
            if strategy.name in self._strategies:
                raise StrategyError(f"Strategy already registered: {strategy.name}")
            strategy.bind_context(
                self.position_provider.get_all,
                lambda: 0.0,
                lambda: MarketRegime.UNSTABLE,
            )
            self._strategies[strategy.name] = strategy
            self._status[strategy.name] = StrategyStatus.STOPPED

    def start_all(self) -> None:
        with self._lock:
            for name in self._strategies:
                if self._strategies[name].config.enabled:
                    self._status[name] = StrategyStatus.RUNNING

    def stop(self, name: str) -> None:
        with self._lock:
            self._ensure_registered(name)
            self._status[name] = StrategyStatus.STOPPED

    def stop_all(self) -> None:
        with self._lock:
            for name in self._status:
                self._status[name] = StrategyStatus.STOPPED

    def pause(self, name: str) -> None:
        with self._lock:
            self._ensure_registered(name)
            self._status[name] = StrategyStatus.PAUSED

    def get_status(self) -> dict[str, StrategyStatus]:
        with self._lock:
            return dict(self._status)

    def on_candle(self, symbol: str, tf: Timeframe, candles: pd.DataFrame) -> list[Signal]:
        emitted: list[Signal] = []
        for strategy in self._running_strategies(symbol, tf):
            try:
                signal = strategy.on_candle(symbol, tf, candles)
                if signal and signal.direction != SignalDirection.HOLD:
                    emitted.append(signal)
                    self._handle_signal(strategy, signal)
            except Exception as exc:
                self._errors[strategy.name].append(exc)
                self._status[strategy.name] = StrategyStatus.ERROR
                if len(self._errors[strategy.name]) >= 3:
                    self._status[strategy.name] = StrategyStatus.DISABLED
        return emitted

    def _handle_signal(self, strategy: StrategyBase, signal: Signal) -> None:
        if self.order_manager is None:
            self._last_signal[strategy.name] = signal
            return
        if self._conflicts(signal):
            if self.conflict_policy == ConflictPolicy.REJECT_NEWER:
                return
            if self.conflict_policy == ConflictPolicy.REJECT_ALL:
                self._last_signal[strategy.name] = signal
                return
        if signal.direction == SignalDirection.CLOSE:
            ticket = int(signal.metadata.get("ticket", 0))
            if ticket:
                self.order_manager.close_order(ticket)
            self._last_signal[strategy.name] = signal
            return
        lot = float(signal.metadata.get("lot", strategy.config.lot))
        order = OrderRequest(
            symbol=signal.symbol,
            order_type=OrderType.BUY if signal.direction == SignalDirection.BUY else OrderType.SELL,
            lot=lot,
            comment=signal.reason,
            magic=strategy.magic,
        )
        self.order_manager.place_market_order(order)
        self._last_signal[strategy.name] = signal

    def _conflicts(self, signal: Signal) -> bool:
        for previous in self._last_signal.values():
            same_symbol = previous.symbol == signal.symbol
            opposite = {previous.direction, signal.direction} == {SignalDirection.BUY, SignalDirection.SELL}
            if same_symbol and opposite:
                return True
        return False

    def _running_strategies(self, symbol: str, tf: Timeframe) -> list[StrategyBase]:
        with self._lock:
            strategies = [strategy for name, strategy in self._strategies.items() if self._status[name] == StrategyStatus.RUNNING and symbol in strategy.symbols and tf in strategy.timeframes]
        return strategies

    def _ensure_registered(self, name: str) -> None:
        if name not in self._strategies:
            raise StrategyError(f"Unknown strategy: {name}")
