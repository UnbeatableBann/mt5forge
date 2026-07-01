"""Market condition classifier."""

from __future__ import annotations

from collections.abc import Callable

from mt5forge.conditions.regime import MarketRegime
from mt5forge.conditions.trend_detector import TrendDetector
from mt5forge.conditions.volatility_meter import VolatilityMeter
from mt5forge.config.trading_config import ConditionsConfig
from mt5forge.core.constants import SpreadState, Timeframe
from mt5forge.core.events import EventBus, RegimeChanged
from mt5forge.market import MarketDataFeed, MarketHours, SpreadMonitor


class MarketConditionClassifier:
    """Classify symbols into regimes and notify subscribers on transitions."""

    def __init__(
        self,
        feed: MarketDataFeed,
        spread_monitor: SpreadMonitor,
        config: ConditionsConfig | None = None,
        event_bus: EventBus | None = None,
        timeframe: Timeframe = Timeframe.H1,
    ) -> None:
        self.feed = feed
        self.spread_monitor = spread_monitor
        self.config = config or ConditionsConfig()
        self.event_bus = event_bus or EventBus()
        self.timeframe = timeframe
        self.trend_detector = TrendDetector(
            self.config.trend_ma_fast,
            self.config.trend_ma_slow,
            self.config.trend_ma_long,
        )
        self.volatility_meter = VolatilityMeter(
            self.config.atr_period,
            self.config.atr_multiplier_high_vol,
        )
        self.market_hours = MarketHours()
        self._last_regime: dict[str, MarketRegime] = {}
        self._callbacks: list[Callable[[MarketRegime], None]] = []

    def classify(self, symbol: str) -> MarketRegime:
        if not self.market_hours.is_open(symbol):
            regime = MarketRegime.MARKET_CLOSED
        else:
            spread_state = self.spread_monitor.sample(symbol).state
            if spread_state == SpreadState.ABNORMAL:
                regime = MarketRegime.ABNORMAL_SPREAD
            else:
                count = max(self.config.trend_ma_long + 25, self.config.atr_period * 4)
                candles = self.feed.get_candles(symbol, self.timeframe, count=count)
                volatility = self.volatility_meter.measure(candles)
                if volatility.high_volatility:
                    regime = MarketRegime.HIGH_VOLATILITY
                elif volatility.low_volatility:
                    regime = MarketRegime.LOW_VOLATILITY
                else:
                    regime = self.trend_detector.detect(candles).regime
        previous = self._last_regime.get(symbol)
        if previous is not None and previous != regime:
            self.event_bus.publish(RegimeChanged(source=__name__, symbol=symbol, old_regime=previous.value, new_regime=regime.value))
            for callback in list(self._callbacks):
                callback(regime)
        self._last_regime[symbol] = regime
        return regime

    def get_recommended_strategies(self, regime: MarketRegime) -> list[str]:
        mapping = {
            MarketRegime.STRONG_BULLISH: ["ma_crossover", "macd"],
            MarketRegime.WEAK_BULLISH: ["macd"],
            MarketRegime.STRONG_BEARISH: ["ma_crossover", "macd"],
            MarketRegime.WEAK_BEARISH: ["macd"],
            MarketRegime.RANGING: ["hedge_recovery"],
            MarketRegime.SIDEWAYS: ["hedge_recovery"],
            MarketRegime.HIGH_VOLATILITY: ["hedge_recovery"],
        }
        return mapping.get(regime, [])

    def subscribe_to_regime_changes(self, callback: Callable[[MarketRegime], None]) -> None:
        self._callbacks.append(callback)
