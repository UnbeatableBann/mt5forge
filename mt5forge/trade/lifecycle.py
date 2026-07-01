"""Full trade lifecycle state machine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from mt5forge.core.constants import TradeState
from mt5forge.core.events import BaseEvent, EventBus, EventType
from mt5forge.orders import OrderManager, OrderRequest, OrderResult


@dataclass(slots=True)
class TradeRecord:
    request: OrderRequest
    result: OrderResult
    state: TradeState
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class TradeLifecycle:
    """Manage PENDING -> PLACED -> OPEN -> MODIFIED -> PARTIAL_CLOSE -> CLOSED."""

    def __init__(self, order_manager: OrderManager, event_bus: EventBus | None = None) -> None:
        self.order_manager = order_manager
        self.event_bus = event_bus or order_manager.event_bus
        self._records: dict[int, TradeRecord] = {}

    def place(self, request: OrderRequest) -> OrderResult:
        result = self.order_manager.place_market_order(request)
        self.register(request, result)
        return result

    def register(self, request: OrderRequest, result: OrderResult) -> TradeRecord:
        state = TradeState.PLACED if result.success else TradeState.PENDING
        record = TradeRecord(request=request, result=result, state=state)
        if result.ticket is not None:
            self._records[result.ticket] = record
        self._publish_state(result.ticket or 0, state)
        return record

    def mark_open(self, ticket: int) -> None:
        self._transition(ticket, TradeState.OPEN)

    def mark_modified(self, ticket: int) -> None:
        self._transition(ticket, TradeState.MODIFIED)

    def mark_partial_close(self, ticket: int) -> None:
        self._transition(ticket, TradeState.PARTIAL_CLOSE)

    def mark_closed(self, ticket: int) -> None:
        self._transition(ticket, TradeState.CLOSED)

    def get(self, ticket: int) -> TradeRecord | None:
        return self._records.get(ticket)

    def _transition(self, ticket: int, state: TradeState) -> None:
        record = self._records.get(ticket)
        if record:
            record.state = state
            record.updated_at = datetime.now(UTC)
            self._publish_state(ticket, state)

    def _publish_state(self, ticket: int, state: TradeState) -> None:
        self.event_bus.publish(
            BaseEvent(
                event_type=EventType.TRADE_STATE_CHANGED,
                source=__name__,
                metadata={"ticket": ticket, "state": state.value},
            )
        )
