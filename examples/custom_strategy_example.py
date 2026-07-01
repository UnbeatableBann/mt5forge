from __future__ import annotations

import pandas as pd

from mt5forge.core import SignalDirection, Timeframe
from mt5forge.indicators import RSI, SMA
from mt5forge.strategies import Signal, StrategyBase, StrategyConfig


class RSIMeanReversionStrategy(StrategyBase):
    name = "rsi_mean_reversion"

    def __init__(self):
        super().__init__(StrategyConfig())

    def on_candle(self, symbol: str, tf: Timeframe, candles: pd.DataFrame):
        signal = None
        if len(candles) >= 200:
            rsi = RSI(candles["close"], 14)
            sma = SMA(candles["close"], 200)
            price = float(candles["close"].iloc[-1])
            if float(rsi.iloc[-1]) < 30 and price > float(sma.iloc[-1]):
                signal = Signal(SignalDirection.BUY, symbol, suggested_sl_pips=25, suggested_tp_pips=50)
            elif float(rsi.iloc[-1]) > 70 and price < float(sma.iloc[-1]):
                signal = Signal(SignalDirection.SELL, symbol, suggested_sl_pips=25, suggested_tp_pips=50)
        return signal
