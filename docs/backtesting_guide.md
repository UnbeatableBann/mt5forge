# Backtesting Guide

Backtests replay OHLCV data through `BacktestRunner`. The runner calls strategy
callbacks on historical candles, fills market orders through `SimulatedBroker`,
applies spread, slippage, and commission, and computes performance analytics.

Metrics include win rate, profit factor, Sharpe, Sortino, Calmar, max drawdown,
recovery factor, streaks, average trade duration, equity curve, drawdown curve,
and signal latency.
