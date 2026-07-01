from __future__ import annotations

from datetime import UTC, datetime

from mt5forge.backtest import BacktestConfig, BacktestRunner, HistoricalDataLoader
from mt5forge.core import Timeframe
from mt5forge.strategies import MACrossoverConfig, MACrossoverStrategy
from tests.mocks.mock_data import sample_candles

if __name__ == "__main__":
    runner = BacktestRunner(data_loader=HistoricalDataLoader.from_dataframe(sample_candles(320)))
    result = runner.run(
        MACrossoverStrategy(MACrossoverConfig(min_trend_strength=0.0)),
        symbol="EURUSD",
        timeframe=Timeframe.H1,
        start=datetime(2024, 1, 1, tzinfo=UTC),
        end=datetime(2024, 1, 15, tzinfo=UTC),
        config=BacktestConfig(initial_balance=10_000),
    )
    print(f"Trades: {result.total_trades} Net profit: {result.net_profit:.2f}")
