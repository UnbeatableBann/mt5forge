# MT5Forge

Production-grade Python trading infrastructure for MetaTrader 5.

MT5Forge is a modular framework that transforms the raw MetaTrader 5 Python API into a structured, extensible, and production-ready trading platform.

Instead of writing trading bots that directly interact with MT5, developers build strategies on top of MT5Forge while the framework handles:

* MT5 connectivity
* Session management
* Market data
* Order execution
* Risk management
* Trade lifecycle
* Notifications
* Monitoring
* Logging
* Backtesting

---

## Why MT5Forge?

Most trading bots eventually become difficult to maintain because strategy logic becomes tightly coupled with:

* MT5 API calls
* Risk management
* Trade management
* Notifications
* Error handling

MT5Forge separates these concerns.

Your strategy only decides:

```python
BUY
SELL
HOLD
```

Everything else is managed by the framework.

---

## Features

### Trading Infrastructure

* MT5 connection management
* Automatic reconnection
* Session validation
* Broker health monitoring

### Market Data

* Candlestick retrieval
* Tick feeds
* Spread monitoring
* Symbol information
* Market hours detection

### Order Execution

* Market orders
* Pending orders
* Order modification
* Partial close support
* Retry policies

### Risk Management

* Dynamic lot sizing
* Drawdown protection
* Daily loss limits
* Exposure controls
* Margin validation

### Trade Management

* Take profit management
* Stop loss management
* Trailing stops
* Breakeven automation
* Trade lifecycle tracking

### Strategies

Built-in strategies:

* Moving Average Crossover
* MACD
* Hedge Recovery

### Notifications

Supported channels:

* Telegram
* Discord
* Slack
* Email
* Webhooks
* Console
* File Logging

### Backtesting

* Historical replay
* Slippage simulation
* Spread simulation
* Performance analytics

---

## Installation

### Requirements

* Python 3.11+
* Windows 10 or Windows 11
* MetaTrader 5 Terminal installed

---

### Install from PyPI

```bash
pip install mt5forge
```

or

```bash
uv add mt5forge
```

---

### Development Installation

```bash
git clone https://github.com/UnbeatableBann/mt5forge.git

cd mt5forge

uv sync

uv pip install -e ".[dev]"
```

---

## Quick Start

### Step 1 – Create Credentials

```python
from mt5forge.connection import MT5Credentials

credentials = MT5Credentials(
    account=12345678,
    password="your_password",
    server="YourBroker-Demo",
)
```

---

### Step 2 – Load Configuration

```python
from mt5forge.config import ConfigLoader

config = ConfigLoader.from_toml(
    "mt5forge.config.toml"
)
```

---

### Step 3 – Create Engine

```python
from mt5forge import TradingEngine

engine = TradingEngine(config)
```

---

### Step 4 – Login

```python
engine.login(credentials)
```

---

### Step 5 – Start Trading

```python
engine.start()
```

---

## First Strategy

```python
from mt5forge.strategies import (
    MACrossoverStrategy,
    MACrossoverConfig,
)

strategy = MACrossoverStrategy(
    MACrossoverConfig(
        fast_ma=21,
        slow_ma=50,
        trend_ma=200,
    )
)

engine.register_strategy(strategy)
engine.start()
```

---

## Market Data Example

```python
from mt5forge.market import MarketDataFeed

feed = MarketDataFeed()

candles = feed.get_candles(
    symbol="EURUSD",
    timeframe="H1",
    count=500,
)

print(candles.tail())
```

---

## Order Execution Example

```python
from mt5forge.orders import OrderRequest
from mt5forge.enums import OrderType

request = OrderRequest(
    symbol="EURUSD",
    order_type=OrderType.BUY,
    lot=0.10,
)

result = engine.order_manager.place_market_order(
    request
)

print(result.success)
```

---

## Custom Strategy Example

```python
from mt5forge.strategies import (
    StrategyBase,
    Signal,
    SignalDirection,
)

class MyStrategy(StrategyBase):

    name = "my_strategy"

    def on_candle(
        self,
        symbol,
        timeframe,
        candles,
    ):
        if condition:
            return Signal(
                direction=SignalDirection.BUY,
                symbol=symbol,
            )

        return None
```

---

## Telegram Notifications

```python
from mt5forge.notifications.channels import (
    TelegramChannel,
)

channel = TelegramChannel(
    config.notifications.telegram
)

engine.notification_bus.register_channel(
    channel
)
```

---

## Running a Backtest

```python
from datetime import datetime

from mt5forge.backtest import (
    BacktestRunner,
)

runner = BacktestRunner(config)

result = runner.run(
    strategy=strategy,
    symbol="EURUSD",
    timeframe="H1",
    start=datetime(2024, 1, 1),
    end=datetime(2024, 12, 31),
)

print(result.net_profit)
print(result.win_rate)
```

---

## Project Structure

```text
mt5forge/
├── core/
├── connection/
├── market/
├── orders/
├── positions/
├── risk/
├── trade/
├── hedge/
├── conditions/
├── indicators/
├── strategies/
├── backtest/
├── notifications/
├── monitoring/
├── logging/
└── config/
```

---

## Documentation

Additional documentation is available in:

```text
docs/
├── architecture.md
├── strategy_guide.md
├── risk_management.md
├── notification_channels.md
├── backtesting_guide.md
└── api_reference.md
```

---

## Running Tests

```bash
uv run pytest
```

Coverage:

```bash
uv run pytest --cov=mt5forge
```

---

## Contributing

```bash
uv run ruff check .

uv run mypy mt5forge

uv run pytest
```

Please ensure all tests pass before submitting changes.

---

## Security

Never commit:

* Broker passwords
* API keys
* Telegram bot tokens
* SMTP credentials

Use environment variables or secure secret storage.

---

## License

MIT License

---

## Disclaimer

This software executes real trades and can result in financial loss.

Always test strategies in a demo environment before deploying to a live account.

Use at your own risk.
