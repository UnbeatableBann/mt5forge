"""Consecutive loss cooldown guard."""

from __future__ import annotations

import time


class TradeCooldown:
    """Pause new trades after configured consecutive losses."""

    def __init__(self, loss_limit: int, cooldown_seconds: int) -> None:
        self.loss_limit = loss_limit
        self.cooldown_seconds = cooldown_seconds
        self.consecutive_losses = 0
        self.cooldown_started_at = 0.0

    def record_trade_result(self, profit: float) -> None:
        if profit < 0:
            self.consecutive_losses += 1
            if self.consecutive_losses >= self.loss_limit:
                self.cooldown_started_at = time.monotonic()
        else:
            self.consecutive_losses = 0
            self.cooldown_started_at = 0.0

    def can_trade(self) -> bool:
        if self.consecutive_losses < self.loss_limit:
            return True
        elapsed = time.monotonic() - self.cooldown_started_at
        if elapsed >= self.cooldown_seconds:
            self.consecutive_losses = 0
            self.cooldown_started_at = 0.0
            return True
        return False
