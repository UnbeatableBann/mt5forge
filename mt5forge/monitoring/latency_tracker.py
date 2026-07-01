"""Execution latency tracking."""

from __future__ import annotations

import statistics
import time
from collections import defaultdict, deque
from collections.abc import Iterator
from contextlib import contextmanager


class ExecutionLatencyTracker:
    """Record latency and expose rolling average and p95 statistics."""

    def __init__(self, threshold_ms: float = 500.0, window: int = 500) -> None:
        self.threshold_ms = threshold_ms
        self.values: deque[float] = deque(maxlen=window)
        self.by_symbol: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=window))

    def record(self, latency_ms: float, symbol: str | None = None) -> bool:
        self.values.append(latency_ms)
        if symbol:
            self.by_symbol[symbol].append(latency_ms)
        return latency_ms > self.threshold_ms

    @contextmanager
    def measure(self, symbol: str | None = None) -> Iterator[None]:
        started = time.perf_counter()
        try:
            yield
        finally:
            self.record((time.perf_counter() - started) * 1000.0, symbol=symbol)

    def average(self, symbol: str | None = None) -> float:
        values = self.by_symbol[symbol] if symbol else self.values
        return statistics.fmean(values) if values else 0.0

    def p95(self, symbol: str | None = None) -> float:
        values = list(self.by_symbol[symbol] if symbol else self.values)
        if not values:
            return 0.0
        if len(values) < 20:
            return max(values)
        return float(statistics.quantiles(values, n=20)[18])
