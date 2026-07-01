"""Hedge orchestration."""

from __future__ import annotations

from mt5forge.core.constants import OrderType
from mt5forge.hedge.hedge_calculator import HedgeCalculator
from mt5forge.hedge.hedge_guard import HedgeGuard, HedgeLayer
from mt5forge.orders import OrderManager, OrderRequest
from mt5forge.positions import PnLCalculator, Position


class HedgeManager:
    """Open counter-trades when primary loss crosses the activation threshold."""

    def __init__(
        self,
        order_manager: OrderManager,
        hedge_calculator: HedgeCalculator | None = None,
        hedge_guard: HedgeGuard | None = None,
        activation_loss_pips: float = 30.0,
    ) -> None:
        self.order_manager = order_manager
        self.hedge_calculator = hedge_calculator or HedgeCalculator()
        self.hedge_guard = hedge_guard or HedgeGuard()
        self.activation_loss_pips = activation_loss_pips
        self.pnl = PnLCalculator()

    def evaluate(self, position: Position) -> int | None:
        direction = "BUY" if position.order_type.is_buy else "SELL"
        loss_pips = -self.pnl.calculate_pnl_pips(
            position.entry_price,
            position.current_price,
            direction,
            position.symbol,
        )
        ticket: int | None = None
        if loss_pips >= self.activation_loss_pips:
            hedge_type = OrderType.SELL if position.order_type.is_buy else OrderType.BUY
            hedge_lot = self.hedge_calculator.calculate_hedge_lot(
                original_lot=position.lot,
                original_entry=position.entry_price,
                current_price=position.current_price,
                original_direction=direction,
                symbol=position.symbol,
            )
            if self.hedge_guard.can_open(position.symbol, hedge_lot):
                result = self.order_manager.place_market_order(
                    OrderRequest(
                        symbol=position.symbol,
                        order_type=hedge_type,
                        lot=hedge_lot,
                        comment=f"hedge_for_{position.ticket}",
                        magic=position.magic,
                    )
                )
                if result.success and result.ticket is not None:
                    self.hedge_guard.record_layer(
                        HedgeLayer(
                            symbol=position.symbol,
                            primary_ticket=position.ticket,
                            hedge_ticket=result.ticket,
                            lot=hedge_lot,
                        )
                    )
                    ticket = result.ticket
        return ticket
