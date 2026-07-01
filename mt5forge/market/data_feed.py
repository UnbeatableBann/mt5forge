"""MT5 market data feed."""

from __future__ import annotations

import threading
from collections.abc import Callable
from datetime import datetime
from typing import Any

import pandas as pd

from mt5forge.connection.connector import MT5Connector
from mt5forge.core.constants import Timeframe
from mt5forge.core.events import BaseEvent, EventBus, EventType
from mt5forge.core.exceptions import MarketDataError
from mt5forge.market.symbol_info import PriceQuote, SymbolInfo, Tick


class MarketDataFeed:
    """Retrieve candles, ticks, prices, and run tick subscriptions."""

    REQUIRED_COLUMNS = ("time", "open", "high", "low", "close", "tick_volume")

    def __init__(self, connector: MT5Connector, event_bus: EventBus | None = None) -> None:
        self.connector = connector
        self.event_bus = event_bus or connector.event_bus
        self._last_candle_time: dict[tuple[str, Timeframe], pd.Timestamp] = {}
        self._subscription_stops: dict[str, threading.Event] = {}
        self._subscription_threads: dict[str, threading.Thread] = {}

    def get_candles(
        self,
        symbol: str,
        timeframe: Timeframe,
        count: int,
        shift: int = 0,
    ) -> pd.DataFrame:
        if count <= 0:
            raise MarketDataError("count must be greater than zero")
        tf = Timeframe.parse(timeframe)
        raw = self.connector.mt5.copy_rates_from_pos(symbol, tf.to_mt5(self.connector.mt5), shift, count)
        if raw is None or len(raw) == 0:
            raise MarketDataError(f"No candle data returned for {symbol} {tf.value}")
        frame = pd.DataFrame(raw)
        if "time" not in frame.columns:
            raise MarketDataError("MT5 candle data did not include a time column")
        frame["time"] = pd.to_datetime(frame["time"], unit="s", utc=True)
        for column in self.REQUIRED_COLUMNS:
            if column not in frame.columns:
                raise MarketDataError(f"Candle data missing required column: {column}")
        if frame[list(self.REQUIRED_COLUMNS)].isna().any().any():
            raise MarketDataError("Candle data contains NaN values")
        frame = frame.sort_values("time").reset_index(drop=True)
        key = (symbol, tf)
        latest_time = pd.Timestamp(frame["time"].iloc[-1])
        previous_time = self._last_candle_time.get(key)
        if previous_time == latest_time:
            self.event_bus.publish(
                BaseEvent(
                    event_type=EventType.ALERT_RAISED,
                    source=__name__,
                    metadata={"alert": "stale_data_detected", "symbol": symbol, "timeframe": tf.value},
                )
            )
        self._last_candle_time[key] = latest_time
        return frame

    def get_tick(self, symbol: str) -> Tick:
        raw = self.connector.mt5.symbol_info_tick(symbol)
        if not raw:
            raise MarketDataError(f"No tick returned for {symbol}")
        return Tick.from_mt5(symbol, raw)

    def get_current_price(self, symbol: str) -> PriceQuote:
        return PriceQuote.from_tick(self.get_tick(symbol))

    def get_symbol_info(self, symbol: str) -> SymbolInfo:
        raw = self.connector.mt5.symbol_info(symbol)
        if not raw:
            raise MarketDataError(f"No symbol info returned for {symbol}")
        return SymbolInfo.from_mt5(raw)

    def subscribe_ticks(self, symbol: str, callback: Callable[[Tick], Any]) -> None:
        stop = threading.Event()
        self._subscription_stops[symbol] = stop
        thread = threading.Thread(
            target=self._poll_ticks,
            args=(symbol, callback, stop),
            name=f"mt5forge-ticks-{symbol}",
            daemon=True,
        )
        self._subscription_threads[symbol] = thread
        thread.start()

    def unsubscribe_ticks(self, symbol: str) -> None:
        stop = self._subscription_stops.get(symbol)
        if stop:
            stop.set()
        thread = self._subscription_threads.get(symbol)
        if thread and thread.is_alive():
            thread.join(timeout=2.0)

    def _poll_ticks(self, symbol: str, callback: Callable[[Tick], Any], stop: threading.Event) -> None:
        last_time: datetime | None = None
        while not stop.wait(0.2):
            tick = self.get_tick(symbol)
            if last_time != tick.time:
                callback(tick)
                last_time = tick.time
