"""Spread monitoring and classification."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass

from mt5forge.core.constants import SpreadState
from mt5forge.market.data_feed import MarketDataFeed


@dataclass(slots=True, frozen=True)
class SpreadSnapshot:
    symbol: str
    spread: float
    average_spread: float
    state: SpreadState


class SpreadMonitor:
    """Track bid-ask spread and classify execution quality."""

    def __init__(self, feed: MarketDataFeed, history_size: int = 200) -> None:
        self.feed = feed
        self.history: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=history_size))

    def sample(self, symbol: str) -> SpreadSnapshot:
        quote = self.feed.get_current_price(symbol)
        self.history[symbol].append(quote.spread)
        average = self.average_spread(symbol)
        state = self.classify(symbol, quote.spread)
        return SpreadSnapshot(symbol=symbol, spread=quote.spread, average_spread=average, state=state)

    def average_spread(self, symbol: str) -> float:
        values = self.history[symbol]
        if not values:
            info = self.feed.get_symbol_info(symbol)
            return info.spread * info.point
        return sum(values) / len(values)

    def classify(self, symbol: str, spread: float | None = None) -> SpreadState:
        current = spread if spread is not None else self.feed.get_current_price(symbol).spread
        average = self.average_spread(symbol)
        baseline = average if average > 0 else current
        if baseline <= 0:
            return SpreadState.NORMAL
        if current > baseline * 5:
            return SpreadState.ABNORMAL
        if current > baseline * 2:
            return SpreadState.ELEVATED
        return SpreadState.NORMAL
