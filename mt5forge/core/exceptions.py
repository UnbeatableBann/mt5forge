"""Custom exception hierarchy for MT5Forge."""

from __future__ import annotations


class MT5ForgeError(Exception):
    """Base class for all package-level errors."""


class ConfigurationError(MT5ForgeError):
    """Raised when configuration data is invalid or unavailable."""


class ConnectionError(MT5ForgeError):
    """Raised when MT5 terminal connection management fails."""


class AuthenticationError(ConnectionError):
    """Raised when MT5 account authentication fails."""


class SessionError(ConnectionError):
    """Raised when broker session validation fails."""


class MarketDataError(MT5ForgeError):
    """Raised when market data retrieval or validation fails."""


class OrderValidationError(MT5ForgeError):
    """Raised when an order fails pre-execution validation."""


class OrderExecutionError(MT5ForgeError):
    """Raised when order execution fails unexpectedly."""


class RiskViolation(MT5ForgeError):
    """Raised when a trade violates configured risk constraints."""


class StrategyError(MT5ForgeError):
    """Raised for strategy registration or runtime failures."""


class HedgeError(MT5ForgeError):
    """Raised when hedge and recovery logic cannot proceed safely."""


class NotificationError(MT5ForgeError):
    """Raised when notification delivery fails."""


class MonitoringError(MT5ForgeError):
    """Raised when watchdog or health monitoring fails."""


class BacktestError(MT5ForgeError):
    """Raised when backtest setup, replay, or analytics fail."""
