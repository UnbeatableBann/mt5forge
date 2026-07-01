from __future__ import annotations

from mt5forge import ConfigLoader, TradingEngine
from mt5forge.notifications.channels import ConsoleChannel
from mt5forge.strategies import MACrossoverConfig, MACrossoverStrategy

if __name__ == "__main__":
    config = ConfigLoader.from_toml("mt5forge.config.toml")
    engine = TradingEngine(config)
    engine.notification_bus.register_channel(ConsoleChannel(config.notifications.console.model_dump()))
    engine.register_strategy(MACrossoverStrategy(MACrossoverConfig()))
    engine.start()
