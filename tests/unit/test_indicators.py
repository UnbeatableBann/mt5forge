from __future__ import annotations

import numpy as np

from mt5forge.indicators import ATR, MACD, RSI, SMA, WMA, BollingerBands, CrossoverDetector, CrossoverType


def test_moving_averages_and_momentum(candles):
    close = candles["close"]
    sma = SMA(close, 5)
    wma = WMA(close, 5)
    macd, signal, hist = MACD(close)
    rsi = RSI(close, 14)
    bands = BollingerBands(close, 20)
    atr = ATR(candles["high"], candles["low"], candles["close"], 14)

    assert np.isclose(float(sma.iloc[-1]), close.tail(5).mean())
    assert float(wma.iloc[-1]) > float(sma.iloc[-1])
    assert len(macd) == len(signal) == len(hist) == len(close)
    assert 0 <= float(rsi.iloc[-1]) <= 100
    assert float(bands.upper.iloc[-1]) > float(bands.lower.iloc[-1])
    assert float(atr.iloc[-1]) > 0


def test_crossover_detector():
    detector = CrossoverDetector()
    event = detector.detect([1, 2, 3], [3, 2, 1])
    assert event is not None
    assert event.type == CrossoverType.BULLISH_CROSS
