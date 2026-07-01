"""Composite hedge recovery strategy."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from mt5forge.conditions import MarketRegime
from mt5forge.core.constants import Timeframe
from mt5forge.market import Tick
from mt5forge.strategies.base import Signal, StrategyBase, StrategyConfig, TradeResult


@dataclass(slots=True)
class HedgeConfig:
    activation_loss_pips: float = 30.0
    target_net_pnl: float = 0.0
    max_layers: int = 2
    recovery_check_interval: int = 60


class HedgeRecoveryStrategy(StrategyBase):
    """Wrap a primary strategy and annotate signals for hedge management."""

    name = "hedge_recovery"

    def __init__(self, primary_strategy: StrategyBase, hedge_config: HedgeConfig) -> None:
        super().__init__(
            StrategyConfig(
                symbols=list(primary_strategy.symbols),
                timeframes=list(primary_strategy.timeframes),
                magic=primary_strategy.magic + 500_000,
                lot=primary_strategy.config.lot,
            )
        )
        self.primary_strategy = primary_strategy
        self.hedge_config = hedge_config

    def on_candle(self, symbol: str, tf: Timeframe, candles: pd.DataFrame) -> Signal | None:
        signal = self.primary_strategy.on_candle(symbol, tf, candles)
        if signal:
            signal.metadata["hedge_recovery_enabled"] = True
            signal.metadata["activation_loss_pips"] = self.hedge_config.activation_loss_pips
            signal.metadata["target_net_pnl"] = self.hedge_config.target_net_pnl
            signal.metadata["max_layers"] = self.hedge_config.max_layers
        return signal

    def on_tick(self, symbol: str, tick: Tick) -> Signal | None:
        return self.primary_strategy.on_tick(symbol, tick)

    def on_trade_closed(self, result: TradeResult) -> None:
        self.primary_strategy.on_trade_closed(result)

    def on_market_condition_change(self, condition: MarketRegime) -> None:
        self.primary_strategy.on_market_condition_change(condition)
