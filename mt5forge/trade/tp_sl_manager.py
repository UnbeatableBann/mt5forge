"""Take-profit and stop-loss manager."""

from __future__ import annotations

from mt5forge.orders import OrderManager, OrderModification
from mt5forge.positions import PnLCalculator, PositionTracker


class TpSlManager:
    """Attach and modify TP/SL values."""

    def __init__(self, order_manager: OrderManager, position_tracker: PositionTracker | None = None) -> None:
        self.order_manager = order_manager
        self.position_tracker = position_tracker or PositionTracker(order_manager.connector)
        self.pnl = PnLCalculator()

    def attach(self, ticket: int, tp: float, sl: float) -> bool:
        return self.order_manager.modify_order(ticket, OrderModification(sl=sl, tp=tp))

    def modify_sl(self, ticket: int, new_sl: float) -> bool:
        return self.order_manager.modify_order(ticket, OrderModification(sl=new_sl))

    def move_to_breakeven(self, ticket: int, buffer_pips: float = 2.0) -> bool:
        position = self.position_tracker.get_by_ticket(ticket)
        if position is None:
            return False
        pip_size = self.pnl.pip_size(position.symbol)
        new_sl = position.entry_price + buffer_pips * pip_size if position.order_type.is_buy else position.entry_price - buffer_pips * pip_size
        return self.modify_sl(ticket, new_sl)
