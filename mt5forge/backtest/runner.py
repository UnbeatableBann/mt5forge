"""Backtest runner."""

from __future__ import annotations

import time
from datetime import datetime

from mt5forge.backtest.analytics import BacktestResult, ComparisonReport, PerformanceAnalytics
from mt5forge.backtest.data_loader import HistoricalDataLoader
from mt5forge.backtest.simulator import SimulatedBroker
from mt5forge.backtest.slippage_sim import SlippageSimulator
from mt5forge.backtest.spread_sim import SpreadSimulator
from mt5forge.config.backtest_config import BacktestConfig
from mt5forge.core.constants import OrderType, SignalDirection, Timeframe
from mt5forge.orders import OrderRequest
from mt5forge.positions import PnLCalculator
from mt5forge.strategies import StrategyBase


class BacktestRunner:
    """Historical replay entry point."""

    def __init__(self, config: BacktestConfig | None = None, data_loader: HistoricalDataLoader | None = None) -> None:
        self.config = config
        self.data_loader = data_loader or HistoricalDataLoader(path=getattr(config, "historical_data_path", ""))
        self.analytics = PerformanceAnalytics()
        self.pnl = PnLCalculator()

    def run(
        self,
        strategy: StrategyBase,
        symbol: str,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
        config: BacktestConfig,
    ) -> BacktestResult:
        started = time.perf_counter()
        data = self.data_loader.load(symbol, timeframe, start, end, path=config.historical_data_path)
        broker = SimulatedBroker(
            initial_balance=config.initial_balance,
            spread_simulator=SpreadSimulator(config.spread_pips),
            slippage_simulator=SlippageSimulator(config.slippage_pips, seed=config.random_seed),
            commission_per_lot=config.commission_per_lot,
        )
        signal_latencies: list[float] = []
        for idx in range(1, len(data)):
            candle = data.iloc[idx]
            historical_slice = data.iloc[: idx + 1]
            broker.process_candle(candle)
            signal_started = time.perf_counter()
            signal = strategy.on_candle(symbol, timeframe, historical_slice)
            signal_latencies.append((time.perf_counter() - signal_started) * 1000.0)
            if signal and signal.direction in {SignalDirection.BUY, SignalDirection.SELL}:
                order_type = OrderType.BUY if signal.direction == SignalDirection.BUY else OrderType.SELL
                price = float(candle["open"])
                sl, tp = self._stops(symbol, price, signal.direction, signal.suggested_sl_pips, signal.suggested_tp_pips)
                broker.place_market_order(
                    OrderRequest(
                        symbol=symbol,
                        order_type=order_type,
                        lot=float(signal.metadata.get("lot", strategy.config.lot)),
                        sl=sl,
                        tp=tp,
                        comment=signal.reason,
                        magic=strategy.magic,
                    ),
                    candle,
                )
        last = data.iloc[-1]
        broker.close_all(float(last["close"]), last["time"].to_pydatetime())
        duration = time.perf_counter() - started
        return self.analytics.compute(
            broker.trades,
            broker.equity_curve,
            config.initial_balance,
            signal_latencies,
            duration,
        )

    def compare(
        self,
        strategies: list[StrategyBase],
        symbol: str,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
    ) -> ComparisonReport:
        backtest_config = getattr(self.config, "backtest", self.config)
        if not isinstance(backtest_config, BacktestConfig):
            backtest_config = BacktestConfig()
        results = {strategy.name: self.run(strategy, symbol, timeframe, start, end, backtest_config) for strategy in strategies}
        return ComparisonReport(results)

    def _stops(
        self,
        symbol: str,
        price: float,
        direction: SignalDirection,
        sl_pips: float | None,
        tp_pips: float | None,
    ) -> tuple[float | None, float | None]:
        pip = self.pnl.pip_size(symbol)
        if direction == SignalDirection.BUY:
            sl = price - sl_pips * pip if sl_pips else None
            tp = price + tp_pips * pip if tp_pips else None
        else:
            sl = price + sl_pips * pip if sl_pips else None
            tp = price - tp_pips * pip if tp_pips else None
        return sl, tp
