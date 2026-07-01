"""Backtesting exports."""

from mt5forge.backtest.analytics import BacktestResult, ComparisonReport, PerformanceAnalytics
from mt5forge.backtest.data_loader import HistoricalDataLoader
from mt5forge.backtest.runner import BacktestRunner
from mt5forge.backtest.simulator import SimulatedBroker, SimulatedPosition, SimulatedTrade
from mt5forge.backtest.slippage_sim import SlippageSimulator
from mt5forge.backtest.spread_sim import SpreadSimulator
from mt5forge.config.backtest_config import BacktestConfig

__all__ = [
    "BacktestConfig",
    "BacktestResult",
    "BacktestRunner",
    "ComparisonReport",
    "HistoricalDataLoader",
    "PerformanceAnalytics",
    "SimulatedBroker",
    "SimulatedPosition",
    "SimulatedTrade",
    "SlippageSimulator",
    "SpreadSimulator",
]
