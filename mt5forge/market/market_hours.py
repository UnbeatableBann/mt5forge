"""Market session detection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta


@dataclass(slots=True, frozen=True)
class MarketSession:
    name: str
    opens: time
    closes: time


class MarketHours:
    """Forex-oriented market hours with weekend closure detection."""

    def __init__(self, sessions: list[MarketSession] | None = None) -> None:
        self.sessions = sessions or [
            MarketSession("asia", time(0, 0), time(8, 0)),
            MarketSession("london", time(8, 0), time(16, 0)),
            MarketSession("new_york", time(13, 0), time(22, 0)),
        ]

    def is_open(self, symbol: str, at: datetime | None = None) -> bool:
        moment = at or datetime.now(UTC)
        if moment.weekday() == 5:
            return False
        if moment.weekday() == 6 and moment.hour < 22:
            return False
        if moment.weekday() == 4 and moment.hour >= 22:
            return False
        return bool(symbol)

    def session_name(self, at: datetime | None = None) -> str:
        moment = at or datetime.now(UTC)
        current = moment.time()
        for session in self.sessions:
            if session.opens <= current < session.closes:
                return session.name
        return "off_hours" if not self.is_open("EURUSD", moment) else "overlap"

    def next_open(self, at: datetime | None = None) -> datetime:
        moment = at or datetime.now(UTC)
        candidate = moment
        for _ in range(8):
            if self.is_open("EURUSD", candidate):
                return candidate
            candidate = candidate + timedelta(hours=1)
        return candidate


TradingHours = MarketHours
