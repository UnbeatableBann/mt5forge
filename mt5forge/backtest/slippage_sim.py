"""Slippage simulation."""

from __future__ import annotations

import random


class SlippageSimulator:
    """Generate deterministic random slippage in pips."""

    def __init__(self, slippage_pips: float = 0.5, seed: int = 42) -> None:
        self.slippage_pips = slippage_pips
        self.random = random.Random(seed)

    def slippage(self) -> float:
        if self.slippage_pips <= 0:
            return 0.0
        return self.random.gauss(0.0, self.slippage_pips / 2.0)
