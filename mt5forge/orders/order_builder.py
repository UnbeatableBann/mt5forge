"""MT5 order request construction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mt5forge.core.constants import DEFAULT_DEVIATION_POINTS, OrderType


@dataclass(slots=True, frozen=True)
class OrderRequest:
    symbol: str
    order_type: OrderType
    lot: float
    sl: float | None = None
    tp: float | None = None
    comment: str = ""
    magic: int = 0
    deviation: int = DEFAULT_DEVIATION_POINTS


@dataclass(slots=True, frozen=True)
class PendingOrderRequest(OrderRequest):
    price: float = 0.0
    expiration: int = 0


@dataclass(slots=True, frozen=True)
class OrderModification:
    sl: float | None = None
    tp: float | None = None
    price: float | None = None
    expiration: int | None = None


@dataclass(slots=True, frozen=True)
class OrderResult:
    success: bool
    ticket: int | None
    error_code: int | None
    error_message: str | None
    executed_price: float | None
    executed_lot: float | None
    latency_ms: float


class OrderBuilder:
    """Build raw request dictionaries accepted by the official MT5 API."""

    def __init__(self, mt5: Any) -> None:
        self.mt5 = mt5

    def build_market_request(self, request: OrderRequest, price: float) -> dict[str, Any]:
        return {
            "action": self._constant("TRADE_ACTION_DEAL", 1),
            "symbol": request.symbol,
            "volume": request.lot,
            "type": self._mt5_order_type(request.order_type),
            "price": price,
            "sl": request.sl or 0.0,
            "tp": request.tp or 0.0,
            "deviation": request.deviation,
            "magic": request.magic,
            "comment": request.comment,
            "type_time": self._constant("ORDER_TIME_GTC", 0),
            "type_filling": self._constant("ORDER_FILLING_IOC", 1),
        }

    def build_pending_request(self, request: PendingOrderRequest) -> dict[str, Any]:
        return {
            "action": self._constant("TRADE_ACTION_PENDING", 5),
            "symbol": request.symbol,
            "volume": request.lot,
            "type": self._mt5_order_type(request.order_type),
            "price": request.price,
            "sl": request.sl or 0.0,
            "tp": request.tp or 0.0,
            "deviation": request.deviation,
            "magic": request.magic,
            "comment": request.comment,
            "type_time": self._constant("ORDER_TIME_GTC", 0),
            "expiration": request.expiration,
            "type_filling": self._constant("ORDER_FILLING_RETURN", 2),
        }

    def build_modification_request(self, ticket: int, modification: OrderModification) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "action": self._constant("TRADE_ACTION_SLTP", 6),
            "position": ticket,
        }
        if modification.sl is not None:
            payload["sl"] = modification.sl
        if modification.tp is not None:
            payload["tp"] = modification.tp
        if modification.price is not None:
            payload["price"] = modification.price
        if modification.expiration is not None:
            payload["expiration"] = modification.expiration
        return payload

    def build_close_request(self, position: Any, lot: float | None = None) -> dict[str, Any]:
        data = position._asdict() if hasattr(position, "_asdict") else dict(position)
        symbol = str(data["symbol"])
        volume = float(lot if lot is not None else data.get("volume", 0.0))
        position_type = int(data.get("type", 0))
        close_type = OrderType.SELL if position_type == 0 else OrderType.BUY
        tick = self.mt5.symbol_info_tick(symbol)
        price = float(tick.bid if close_type == OrderType.SELL else tick.ask)
        return {
            "action": self._constant("TRADE_ACTION_DEAL", 1),
            "symbol": symbol,
            "volume": volume,
            "type": self._mt5_order_type(close_type),
            "position": int(data["ticket"]),
            "price": price,
            "deviation": DEFAULT_DEVIATION_POINTS,
            "magic": int(data.get("magic", 0)),
            "comment": "mt5forge close",
            "type_time": self._constant("ORDER_TIME_GTC", 0),
            "type_filling": self._constant("ORDER_FILLING_IOC", 1),
        }

    def _mt5_order_type(self, order_type: OrderType) -> int:
        mapping = {
            OrderType.BUY: ("ORDER_TYPE_BUY", 0),
            OrderType.SELL: ("ORDER_TYPE_SELL", 1),
            OrderType.BUY_LIMIT: ("ORDER_TYPE_BUY_LIMIT", 2),
            OrderType.SELL_LIMIT: ("ORDER_TYPE_SELL_LIMIT", 3),
            OrderType.BUY_STOP: ("ORDER_TYPE_BUY_STOP", 4),
            OrderType.SELL_STOP: ("ORDER_TYPE_SELL_STOP", 5),
            OrderType.BUY_STOP_LIMIT: ("ORDER_TYPE_BUY_STOP_LIMIT", 6),
            OrderType.SELL_STOP_LIMIT: ("ORDER_TYPE_SELL_STOP_LIMIT", 7),
        }
        attr, fallback = mapping[order_type]
        return self._constant(attr, fallback)

    def _constant(self, name: str, fallback: int) -> int:
        return int(getattr(self.mt5, name, fallback))
