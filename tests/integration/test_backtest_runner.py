from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from mt5forge.backtest import BacktestConfig, BacktestRunner, HistoricalDataLoader
from mt5forge.core.constants import SignalDirection, Timeframe
from mt5forge.strategies import Signal, StrategyBase, StrategyConfig
from tests.mocks.mock_data import sample_candles


class FirstBarStrategy(StrategyBase):
    name = "first_bar"

    def __init__(self):
        super().__init__(StrategyConfig(lot=0.1))
        self.done = False

    def on_candle(self, symbol: str, tf: Timeframe, candles: pd.DataFrame):
        signal = None
        if not self.done and len(candles) > 5:
            self.done = True
            signal = Signal(
                SignalDirection.BUY,
                symbol=symbol,
                suggested_sl_pips=20,
                suggested_tp_pips=40,
                reason="first opportunity",
            )
        return signal


def test_backtest_runner_computes_metrics():
    data = sample_candles(80)
    loader = HistoricalDataLoader.from_dataframe(data)
    runner = BacktestRunner(data_loader=loader)
    result = runner.run(
        FirstBarStrategy(),
        "EURUSD",
        Timeframe.H1,
        datetime(2024, 1, 1, tzinfo=UTC),
        datetime(2024, 1, 5, tzinfo=UTC),
        BacktestConfig(initial_balance=10_000, spread_pips=1.0, slippage_pips=0.0),
    )
    assert result.total_trades >= 1
    assert result.equity_curve.size > 0
