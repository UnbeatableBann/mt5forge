"""Pre-execution order validation."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from mt5forge.market.market_hours import MarketHours
from mt5forge.market.symbol_info import PriceQuote, SymbolInfo
from mt5forge.orders.order_builder import OrderRequest, PendingOrderRequest


@dataclass(slots=True, frozen=True)
class ValidationResult:
    approved: bool
    reasons: tuple[str, ...] = field(default_factory=tuple)


class OrderValidator:
    """Validate market state, lot bounds, stops, margin hints, and duplicates."""

    def __init__(self, market_hours: MarketHours | None = None, duplicate_window_seconds: float = 5.0) -> None:
        self.market_hours = market_hours or MarketHours()
        self.duplicate_window_seconds = duplicate_window_seconds
        self._recent_requests: dict[tuple[str, str], float] = {}

    def validate(
        self,
        request: OrderRequest,
        symbol_info: SymbolInfo,
        quote: PriceQuote,
        margin_free: float | None = None,
    ) -> ValidationResult:
        reasons: list[str] = []
        if not self.market_hours.is_open(request.symbol):
            reasons.append("market_closed")
        if not symbol_info.is_tradeable:
            reasons.append("symbol_not_tradeable")
        if request.lot < symbol_info.volume_min or request.lot > symbol_info.volume_max:
            reasons.append("lot_outside_symbol_bounds")
        if symbol_info.volume_step > 0:
            steps = round((request.lot - symbol_info.volume_min) / symbol_info.volume_step)
            normalized = symbol_info.volume_min + steps * symbol_info.volume_step
            if abs(normalized - request.lot) > 1e-8:
                reasons.append("lot_not_aligned_to_step")
        price = quote.ask if request.order_type.is_buy else quote.bid
        min_distance = symbol_info.point * max(symbol_info.spread, 1.0)
        if request.sl is not None and abs(price - request.sl) < min_distance:
            reasons.append("stop_loss_too_close")
        if request.tp is not None and abs(price - request.tp) < min_distance:
            reasons.append("take_profit_too_close")
        if isinstance(request, PendingOrderRequest) and request.price <= 0:
            reasons.append("pending_price_required")
        if margin_free is not None and margin_free <= 0:
            reasons.append("insufficient_margin")
        key = (request.symbol, request.order_type.value)
        now = time.monotonic()
        last = self._recent_requests.get(key)
        if last is not None and now - last < self.duplicate_window_seconds:
            reasons.append("duplicate_request_cooldown")
        approved = not reasons
        if approved:
            self._recent_requests[key] = now
        return ValidationResult(approved=approved, reasons=tuple(reasons))
