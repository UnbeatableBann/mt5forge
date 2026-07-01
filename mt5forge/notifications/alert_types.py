"""Alert type and severity enums."""

from __future__ import annotations

from enum import StrEnum


class AlertSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    @property
    def rank(self) -> int:
        return {
            AlertSeverity.INFO: 10,
            AlertSeverity.WARNING: 20,
            AlertSeverity.ERROR: 30,
            AlertSeverity.CRITICAL: 40,
        }[self]


class AlertType(StrEnum):
    TRADE_OPENED = "trade_opened"
    TRADE_CLOSED = "trade_closed"
    TRADE_MODIFIED = "trade_modified"
    ORDER_REJECTED = "order_rejected"
    PARTIAL_CLOSE = "partial_close"
    DRAWDOWN_WARNING = "drawdown_warning"
    DAILY_LOSS_LIMIT_HIT = "daily_loss_limit_hit"
    RISK_VIOLATION = "risk_violation"
    MARGIN_WARNING = "margin_warning"
    HEDGE_ACTIVATED = "hedge_activated"
    HEDGE_ESCALATION = "hedge_escalation"
    RECOVERY_ACTIVATED = "recovery_activated"
    HEDGE_CLOSED = "hedge_closed"
    MT5_DISCONNECTED = "mt5_disconnected"
    MT5_RECONNECTED = "mt5_reconnected"
    TERMINAL_FROZEN = "terminal_frozen"
    STRATEGY_FAILURE = "strategy_failure"
    ABNORMAL_SPREAD = "abnormal_spread"
    MARKET_CLOSED = "market_closed"
    REGIME_CHANGE = "regime_change"
    HIGH_VOLATILITY = "high_volatility"
    LARGE_PROFIT = "large_profit"
    LARGE_LOSS = "large_loss"
    CONSECUTIVE_LOSSES = "consecutive_losses"
    RETRY_FAILURE = "retry_failure"
    NOTIFICATION_FAILURE = "notification_failure"
    STALE_DATA_DETECTED = "stale_data_detected"
