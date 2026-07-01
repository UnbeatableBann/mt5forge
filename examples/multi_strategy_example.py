from __future__ import annotations

from mt5forge.strategies import (
    HedgeConfig,
    HedgeRecoveryStrategy,
    MACDStrategy,
    MACDStrategyConfig,
    MACrossoverConfig,
    MACrossoverStrategy,
    StrategyRunner,
)

if __name__ == "__main__":
    runner = StrategyRunner()
    primary = MACrossoverStrategy(MACrossoverConfig())
    runner.register(HedgeRecoveryStrategy(primary, HedgeConfig()))
    runner.register(MACDStrategy(MACDStrategyConfig()))
    runner.start_all()
    print(runner.get_status())
