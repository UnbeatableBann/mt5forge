from __future__ import annotations

import pandas as pd

from mt5forge.core.constants import SignalDirection, Timeframe
from mt5forge.strategies import Signal, StrategyBase, StrategyConfig, StrategyRunner


class BuyOnceStrategy(StrategyBase):
    name = "buy_once"

    def __init__(self):
        super().__init__(StrategyConfig())
        self.sent = False

    def on_candle(self, symbol: str, tf: Timeframe, candles: pd.DataFrame):
        signal = None
        if not self.sent:
            self.sent = True
            signal = Signal(SignalDirection.BUY, symbol=symbol, reason="test")
        return signal


def test_strategy_runner_dispatches_signals(candles):
    runner = StrategyRunner()
    runner.register(BuyOnceStrategy())
    runner.start_all()
    signals = runner.on_candle("EURUSD", Timeframe.H1, candles)
    assert len(signals) == 1
    assert signals[0].direction == SignalDirection.BUY
