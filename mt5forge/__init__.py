"""Public API for MT5Forge."""

from mt5forge.config import BacktestConfig, ConfigLoader, RiskConfig, TradingConfig
from mt5forge.connection.connector import MT5Connector, MT5Credentials
from mt5forge.core.constants import OrderType, SignalDirection, Timeframe
from mt5forge.core.engine import TradingEngine
from mt5forge.strategies.base import Signal, StrategyBase, StrategyConfig

__all__ = [
    "BacktestConfig",
    "ConfigLoader",
    "MT5Connector",
    "MT5Credentials",
    "OrderType",
    "RiskConfig",
    "Signal",
    "SignalDirection",
    "StrategyBase",
    "StrategyConfig",
    "Timeframe",
    "TradingConfig",
    "TradingEngine",
]
