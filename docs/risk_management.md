# Risk Management

`RiskManager` is the central gatekeeper for execution. It enforces:

- lot floor and cap
- max daily loss
- max drawdown
- concurrent trade limits
- per-symbol exposure
- minimum margin level
- consecutive loss cooldown
- hedge exposure cap

`OrderManager` calls `RiskManager.validate_order` before any MT5 `order_send`.
