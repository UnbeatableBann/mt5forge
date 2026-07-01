"""Trading engine orchestrator."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from mt5forge.config.trading_config import TradingConfig
from mt5forge.connection import BrokerHealthMonitor, MT5Connector, SessionManager
from mt5forge.core.events import EventBus
from mt5forge.logging import configure_logging, get_logger

if TYPE_CHECKING:
    from mt5forge.strategies.base import StrategyBase


class TradingEngine:
    """Main user-facing orchestrator for live MT5 trading infrastructure."""

    def __init__(self, config: TradingConfig) -> None:
        self.config = config
        self.logger = configure_logging(config.logging)
        self.event_bus = EventBus()
        self.connector = MT5Connector(
            terminal_path=config.mt5.terminal_path,
            event_bus=self.event_bus,
            reconnect_attempts=config.mt5.reconnect_attempts,
            reconnect_delay_base=config.mt5.reconnect_delay_base,
            reconnect_delay_max=config.mt5.reconnect_delay_max,
        )
        self.session_manager = SessionManager(self.connector)
        self.health_monitor = BrokerHealthMonitor(
            self.connector,
            event_bus=self.event_bus,
            interval_seconds=float(config.monitoring.broker_check_interval),
        )

        from mt5forge.market import MarketDataFeed, SpreadMonitor
        from mt5forge.notifications import NotificationBus
        from mt5forge.orders import OrderManager
        from mt5forge.positions import PositionTracker
        from mt5forge.risk import RiskManager
        from mt5forge.strategies import StrategyRunner

        self.notification_bus = NotificationBus(config.notifications)
        self.position_tracker = PositionTracker(self.connector)
        self.market_data = MarketDataFeed(self.connector, self.event_bus)
        self.spread_monitor = SpreadMonitor(self.market_data)
        self.risk_manager = RiskManager(config.risk, self.event_bus)
        self.order_manager = OrderManager(
            connector=self.connector,
            risk_manager=self.risk_manager,
            event_bus=self.event_bus,
        )
        self.strategy_runner = StrategyRunner(
            order_manager=self.order_manager,
            risk_manager=self.risk_manager,
            position_provider=self.position_tracker,
            event_bus=self.event_bus,
            conflict_policy=config.trading.conflict_policy,
        )
        self._stop = threading.Event()
        self._engine_logger = get_logger(__name__)

    def register_strategy(self, strategy: StrategyBase) -> None:
        self.strategy_runner.register(strategy)

    def start(self) -> None:
        self.connector.initialize()
        credentials = self.config.mt5.credentials()
        if credentials.account and credentials.password and credentials.server:
            self.connector.login(credentials)
        self.health_monitor.start()
        self.strategy_runner.start_all()
        self._engine_logger.info("trading_engine_started")
        while not self._stop.wait(1.0):
            self.health_monitor.check_once()

    def stop(self) -> None:
        self._stop.set()
        self.strategy_runner.stop_all()
        self.health_monitor.stop()
        self.connector.shutdown()
        self._engine_logger.info("trading_engine_stopped")
