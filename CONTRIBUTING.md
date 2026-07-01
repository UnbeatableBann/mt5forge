# Contributing

MT5Forge is organized by infrastructure layer. New strategies should inherit
`StrategyBase`, emit typed `Signal` objects, and rely on the existing runner,
risk manager, order manager, and trade lifecycle instead of calling MT5 APIs
directly.

Before opening changes, run:

```bash
uv sync
uv run pytest
uv build
```
