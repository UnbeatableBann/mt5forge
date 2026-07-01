# Strategy Guide

Strategies inherit `StrategyBase` and implement `on_candle`. They analyze
market data and return `Signal` objects with `BUY`, `SELL`, `CLOSE`, or `HOLD`.

Built-in strategies:

- `MACrossoverStrategy`
- `MACDStrategy`
- `HedgeRecoveryStrategy`

Strategies must not call MT5 directly. The runner translates signals into order
requests and sends them through risk and execution infrastructure.
