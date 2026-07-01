"""Strategy framework and built-in strategies."""

from mt5forge.strategies.base import Signal, StrategyBase, StrategyConfig, TradeResult
from mt5forge.strategies.hedge_recovery import HedgeConfig, HedgeRecoveryStrategy
from mt5forge.strategies.ma_crossover import MACrossoverConfig, MACrossoverStrategy
from mt5forge.strategies.macd_strategy import MACDStrategy, MACDStrategyConfig
from mt5forge.strategies.registry import StrategyRegistry
from mt5forge.strategies.runner import StrategyRunner

__all__ = [
    "HedgeConfig",
    "HedgeRecoveryStrategy",
    "MACDStrategy",
    "MACDStrategyConfig",
    "MACrossoverConfig",
    "MACrossoverStrategy",
    "Signal",
    "StrategyBase",
    "StrategyConfig",
    "StrategyRegistry",
    "StrategyRunner",
    "TradeResult",
]
