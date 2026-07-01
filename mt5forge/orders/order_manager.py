"""Central order execution manager."""

from __future__ import annotations

import time
from typing import Any

from mt5forge.connection.connector import MT5Connector
from mt5forge.core.events import EventBus, OrderClosed, OrderPlaced, RiskRejected
from mt5forge.core.exceptions import OrderExecutionError
from mt5forge.market.symbol_info import PriceQuote, SymbolInfo, Tick
from mt5forge.orders.order_builder import (
    OrderBuilder,
    OrderModification,
    OrderRequest,
    OrderResult,
    PendingOrderRequest,
)
from mt5forge.orders.order_tracker import OrderTracker
from mt5forge.orders.order_validator import OrderValidator
from mt5forge.orders.retry import RetryPolicy
from mt5forge.risk.risk_manager import RiskManager


class OrderManager:
    """Only component allowed to send orders to MT5."""

    def __init__(
        self,
        connector: MT5Connector,
        risk_manager: RiskManager,
        event_bus: EventBus | None = None,
        validator: OrderValidator | None = None,
        retry_policy: RetryPolicy | None = None,
        tracker: OrderTracker | None = None,
    ) -> None:
        self.connector = connector
        self.risk_manager = risk_manager
        self.event_bus = event_bus or connector.event_bus
        self.validator = validator or OrderValidator()
        self.retry_policy = retry_policy or RetryPolicy()
        self.tracker = tracker or OrderTracker()
        self.builder = OrderBuilder(connector.mt5)

    def place_market_order(self, request: OrderRequest) -> OrderResult:
        quote = self._quote(request.symbol)
        symbol_info = self._symbol_info(request.symbol)
        account_info = self._account_info()
        positions = self._positions()
        risk = self.risk_manager.validate_order(request, account_info=account_info, positions=positions)
        if not risk.approved:
            reason = ", ".join(risk.reasons)
            self.event_bus.publish(RiskRejected(source=__name__, symbol=request.symbol, reason=reason))
            return self._failed(None, None, reason, 0.0)
        validation = self.validator.validate(request, symbol_info, quote, account_info.get("margin_free"))
        if not validation.approved:
            reason = ", ".join(validation.reasons)
            return self._failed(None, None, reason, 0.0)
        price = quote.ask if request.order_type.is_buy else quote.bid
        payload = self.builder.build_market_request(request, price)
        result = self._send(payload)
        self.tracker.record(result)
        if result.success and result.ticket is not None:
            self.event_bus.publish(OrderPlaced(source=__name__, ticket=result.ticket, symbol=request.symbol))
        return result

    def place_pending_order(self, request: PendingOrderRequest) -> OrderResult:
        quote = self._quote(request.symbol)
        symbol_info = self._symbol_info(request.symbol)
        account_info = self._account_info()
        positions = self._positions()
        risk = self.risk_manager.validate_order(request, account_info=account_info, positions=positions)
        if not risk.approved:
            reason = ", ".join(risk.reasons)
            self.event_bus.publish(RiskRejected(source=__name__, symbol=request.symbol, reason=reason))
            return self._failed(None, None, reason, 0.0)
        validation = self.validator.validate(request, symbol_info, quote, account_info.get("margin_free"))
        if not validation.approved:
            return self._failed(None, None, ", ".join(validation.reasons), 0.0)
        result = self._send(self.builder.build_pending_request(request))
        self.tracker.record(result)
        if result.success and result.ticket is not None:
            self.event_bus.publish(OrderPlaced(source=__name__, ticket=result.ticket, symbol=request.symbol))
        return result

    def modify_order(self, ticket: int, modification: OrderModification) -> bool:
        payload = self.builder.build_modification_request(ticket, modification)
        result = self._send(payload)
        return result.success

    def close_order(self, ticket: int, lot: float | None = None) -> bool:
        if not self.risk_manager.validate_close(ticket).approved:
            return False
        positions = self.connector.mt5.positions_get(ticket=ticket) or []
        position = next(iter(positions), None)
        if position is None:
            return False
        payload = self.builder.build_close_request(position, lot)
        result = self._send(payload)
        if result.success:
            data = position._asdict() if hasattr(position, "_asdict") else dict(position)
            self.event_bus.publish(
                OrderClosed(
                    source=__name__,
                    ticket=ticket,
                    symbol=str(data.get("symbol", "")),
                    profit=float(data.get("profit", 0.0)),
                )
            )
        return result.success

    def close_all(self, symbol: str | None = None) -> list[OrderResult]:
        raw_positions = self.connector.mt5.positions_get(symbol=symbol) if symbol else self.connector.mt5.positions_get()
        results: list[OrderResult] = []
        for position in raw_positions or []:
            payload = self.builder.build_close_request(position)
            results.append(self._send(payload))
        return results

    def _send(self, payload: dict[str, Any]) -> OrderResult:
        started = time.perf_counter()

        def operation() -> Any:
            return self.connector.mt5.order_send(payload)

        raw = self.retry_policy.execute(operation, lambda item: int(getattr(item, "retcode", 0)) if item else 0)
        latency = (time.perf_counter() - started) * 1000.0
        if not raw:
            return self._failed(None, 0, "order_send_returned_empty", latency)
        data = raw._asdict() if hasattr(raw, "_asdict") else dict(raw)
        retcode = int(data.get("retcode", 0))
        success_codes = {
            int(getattr(self.connector.mt5, "TRADE_RETCODE_DONE", 10009)),
            int(getattr(self.connector.mt5, "TRADE_RETCODE_PLACED", 10008)),
        }
        success = retcode in success_codes
        ticket = data.get("order", data.get("deal"))
        return OrderResult(
            success=success,
            ticket=int(ticket) if ticket else None,
            error_code=None if success else retcode,
            error_message=None if success else str(data.get("comment", "execution_failed")),
            executed_price=float(data.get("price", 0.0)) if data.get("price") is not None else None,
            executed_lot=float(data.get("volume", 0.0)) if data.get("volume") is not None else None,
            latency_ms=latency,
        )

    @staticmethod
    def _failed(
        ticket: int | None,
        code: int | None,
        message: str | None,
        latency_ms: float,
    ) -> OrderResult:
        return OrderResult(
            success=False,
            ticket=ticket,
            error_code=code,
            error_message=message,
            executed_price=None,
            executed_lot=None,
            latency_ms=latency_ms,
        )

    def _quote(self, symbol: str) -> PriceQuote:
        tick_raw = self.connector.mt5.symbol_info_tick(symbol)
        if not tick_raw:
            raise OrderExecutionError(f"No tick available for {symbol}")
        return PriceQuote.from_tick(Tick.from_mt5(symbol, tick_raw))

    def _symbol_info(self, symbol: str) -> SymbolInfo:
        raw = self.connector.mt5.symbol_info(symbol)
        if not raw:
            raise OrderExecutionError(f"No symbol info available for {symbol}")
        return SymbolInfo.from_mt5(raw)

    def _account_info(self) -> dict[str, float]:
        raw = self.connector.mt5.account_info()
        if not raw:
            return {}
        data = raw._asdict() if hasattr(raw, "_asdict") else dict(raw)
        return {
            "balance": float(data.get("balance", 0.0)),
            "equity": float(data.get("equity", 0.0)),
            "margin_level": float(data.get("margin_level", 0.0)),
            "margin_free": float(data.get("margin_free", data.get("free_margin", 0.0))),
        }

    def _positions(self) -> list[Any]:
        return list(self.connector.mt5.positions_get() or [])
