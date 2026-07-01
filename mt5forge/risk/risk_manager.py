"""Central risk gatekeeper."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from mt5forge.config.risk_config import RiskConfig
from mt5forge.core.events import EventBus, RiskRejected
from mt5forge.orders.order_builder import OrderRequest
from mt5forge.risk.cooldown import TradeCooldown
from mt5forge.risk.drawdown_guard import DrawdownGuard
from mt5forge.risk.exposure_monitor import ExposureMonitor
from mt5forge.risk.lot_calculator import LotCalculator


@dataclass(slots=True, frozen=True)
class RiskDecision:
    approved: bool
    reasons: tuple[str, ...] = field(default_factory=tuple)
    adjusted_lot: float | None = None


class RiskManager:
    """Mandatory gate for every execution path."""

    def __init__(self, config: RiskConfig, event_bus: EventBus | None = None) -> None:
        self.config = config
        self.event_bus = event_bus or EventBus()
        self.lot_calculator = LotCalculator(config)
        self.drawdown_guard = DrawdownGuard(config.max_drawdown_pct)
        self.exposure_monitor = ExposureMonitor(config)
        self.cooldown = TradeCooldown(config.consecutive_loss_limit, config.cooldown_after_loss_seconds)
        self._day = date.today()
        self._daily_realized_pnl = 0.0
        self._starting_balance = 0.0

    def validate_order(
        self,
        request: OrderRequest,
        account_info: dict[str, float] | None = None,
        positions: list[Any] | None = None,
        is_hedge: bool = False,
    ) -> RiskDecision:
        account = account_info or {}
        open_positions = positions or []
        reasons: list[str] = []
        balance = float(account.get("balance", self._starting_balance or 0.0))
        equity = float(account.get("equity", balance))
        if self._starting_balance <= 0 and balance > 0:
            self._starting_balance = balance
        if not self.cooldown.can_trade():
            reasons.append("trade_cooldown_active")
        if request.lot < self.config.min_lot_size:
            reasons.append("below_min_lot_size")
        if request.lot > self.config.max_lot_size:
            reasons.append("above_max_lot_size")
        margin_level = float(account.get("margin_level", self.config.margin_level_minimum))
        if margin_level and margin_level < self.config.margin_level_minimum:
            reasons.append("margin_level_below_minimum")
        if self._starting_balance > 0:
            max_daily_loss = self._starting_balance * (self.config.max_daily_loss_pct / 100.0)
            if abs(min(self._daily_realized_pnl, 0.0)) >= max_daily_loss:
                reasons.append("max_daily_loss_hit")
        drawdown = self.drawdown_guard.update(equity)
        if drawdown.paused:
            reasons.append("max_drawdown_hit")
        reasons.extend(self.exposure_monitor.validate(request.symbol, request.order_type, request.lot, open_positions, is_hedge))
        approved = not reasons
        decision = RiskDecision(
            approved=approved,
            reasons=tuple(reasons),
            adjusted_lot=min(max(request.lot, self.config.min_lot_size), self.config.max_lot_size),
        )
        if not approved:
            self.event_bus.publish(RiskRejected(source=__name__, symbol=request.symbol, reason=", ".join(decision.reasons)))
        return decision

    def validate_close(self, ticket: int) -> RiskDecision:
        reason = "invalid_ticket" if ticket <= 0 else ""
        return RiskDecision(approved=not reason, reasons=(reason,) if reason else ())

    def record_trade_close(self, profit: float) -> None:
        today = date.today()
        if today != self._day:
            self._day = today
            self._daily_realized_pnl = 0.0
        self._daily_realized_pnl += profit
        self.cooldown.record_trade_result(profit)
