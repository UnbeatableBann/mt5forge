"""Market regime enum and transitions."""

from __future__ import annotations

from enum import StrEnum


class MarketRegime(StrEnum):
    STRONG_BULLISH = "strong_bullish"
    WEAK_BULLISH = "weak_bullish"
    RANGING = "ranging"
    SIDEWAYS = "sideways"
    WEAK_BEARISH = "weak_bearish"
    STRONG_BEARISH = "strong_bearish"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    ABNORMAL_SPREAD = "abnormal_spread"
    UNSTABLE = "unstable"
    MARKET_CLOSED = "market_closed"

    @property
    def supports_trend_following(self) -> bool:
        return self in {
            MarketRegime.STRONG_BULLISH,
            MarketRegime.WEAK_BULLISH,
            MarketRegime.WEAK_BEARISH,
            MarketRegime.STRONG_BEARISH,
        }
