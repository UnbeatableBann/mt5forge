# Architecture

MT5Forge is organized as a standalone Python package. Strategies emit typed
signals, the `RiskManager` validates every order, `OrderManager` performs MT5
execution, and lifecycle, hedge, monitoring, logging, and notification layers
observe the same typed event flow.

Live trading uses `MT5Connector` and `SessionManager`; backtests use
`SimulatedBroker` and `HistoricalDataLoader` without importing MT5.
