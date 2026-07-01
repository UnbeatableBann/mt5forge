"""Typed symbol and tick models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from mt5forge.core.constants import DEFAULT_PIP_SIZE, JPY_PIP_SIZE


@dataclass(slots=True, frozen=True)
class Tick:
    symbol: str
    bid: float
    ask: float
    last: float
    volume: float
    time: datetime

    @classmethod
    def from_mt5(cls, symbol: str, raw: Any) -> Tick:
        data = raw._asdict() if hasattr(raw, "_asdict") else dict(raw)
        timestamp = data.get("time_msc", data.get("time", 0))
        seconds = float(timestamp) / 1000.0 if timestamp and timestamp > 10_000_000_000 else float(timestamp)
        return cls(
            symbol=symbol,
            bid=float(data.get("bid", 0.0)),
            ask=float(data.get("ask", 0.0)),
            last=float(data.get("last", data.get("bid", 0.0))),
            volume=float(data.get("volume_real", data.get("volume", 0.0))),
            time=datetime.fromtimestamp(seconds, tz=UTC) if seconds else datetime.now(UTC),
        )


@dataclass(slots=True, frozen=True)
class PriceQuote:
    symbol: str
    bid: float
    ask: float
    mid: float
    spread: float
    timestamp: datetime

    @classmethod
    def from_tick(cls, tick: Tick) -> PriceQuote:
        mid = (tick.bid + tick.ask) / 2.0
        return cls(
            symbol=tick.symbol,
            bid=tick.bid,
            ask=tick.ask,
            mid=mid,
            spread=max(tick.ask - tick.bid, 0.0),
            timestamp=tick.time,
        )


@dataclass(slots=True, frozen=True)
class SymbolInfo:
    name: str
    trade_mode: int
    volume_min: float
    volume_max: float
    volume_step: float
    contract_size: float
    point: float
    digits: int
    spread: float
    currency_profit: str = "USD"
    currency_margin: str = "USD"

    @property
    def pip_size(self) -> float:
        return JPY_PIP_SIZE if self.name.endswith("JPY") else DEFAULT_PIP_SIZE

    @property
    def pip_value_per_lot(self) -> float:
        value = self.contract_size * self.pip_size
        return value if value > 0 else 10.0

    @property
    def is_tradeable(self) -> bool:
        return self.trade_mode not in {0, 2}

    @classmethod
    def from_mt5(cls, raw: Any) -> SymbolInfo:
        data = raw._asdict() if hasattr(raw, "_asdict") else dict(raw)
        return cls(
            name=str(data.get("name", "")),
            trade_mode=int(data.get("trade_mode", 0)),
            volume_min=float(data.get("volume_min", 0.01)),
            volume_max=float(data.get("volume_max", 100.0)),
            volume_step=float(data.get("volume_step", 0.01)),
            contract_size=float(data.get("trade_contract_size", data.get("contract_size", 100_000.0))),
            point=float(data.get("point", DEFAULT_PIP_SIZE / 10.0)),
            digits=int(data.get("digits", 5)),
            spread=float(data.get("spread", 0.0)),
            currency_profit=str(data.get("currency_profit", "USD")),
            currency_margin=str(data.get("currency_margin", "USD")),
        )
