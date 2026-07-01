"""Strategy registry."""

from __future__ import annotations

from collections.abc import Callable

from mt5forge.core.exceptions import StrategyError
from mt5forge.strategies.base import StrategyBase, StrategyConfig


class StrategyRegistry:
    """Register and instantiate strategies by name."""

    def __init__(self) -> None:
        self._factories: dict[str, Callable[[StrategyConfig], StrategyBase]] = {}

    def register(self, name: str, factory: Callable[[StrategyConfig], StrategyBase]) -> None:
        if name in self._factories:
            raise StrategyError(f"Strategy factory already exists: {name}")
        self._factories[name] = factory

    def create(self, name: str, config: StrategyConfig) -> StrategyBase:
        factory = self._factories.get(name)
        if factory is None:
            raise StrategyError(f"Strategy factory not found: {name}")
        return factory(config)

    def names(self) -> list[str]:
        return sorted(self._factories)
