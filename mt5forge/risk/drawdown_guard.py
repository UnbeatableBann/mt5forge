"""Portfolio drawdown protection."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class DrawdownStatus:
    equity: float
    peak_equity: float
    drawdown: float
    drawdown_pct: float
    paused: bool
    alerts: tuple[str, ...] = field(default_factory=tuple)


class DrawdownGuard:
    """Track running drawdown and pause trading past configured limits."""

    def __init__(self, max_drawdown_pct: float, resume_pct: float | None = None) -> None:
        self.max_drawdown_pct = max_drawdown_pct
        self.resume_pct = resume_pct if resume_pct is not None else max_drawdown_pct * 0.75
        self.peak_equity = 0.0
        self.paused = False
        self._fired_thresholds: set[float] = set()

    def update(self, equity: float) -> DrawdownStatus:
        self.peak_equity = max(self.peak_equity, equity)
        drawdown = max(self.peak_equity - equity, 0.0)
        drawdown_pct = (drawdown / self.peak_equity * 100.0) if self.peak_equity > 0 else 0.0
        alerts: list[str] = []
        for fraction in (0.5, 0.75, 0.9):
            threshold = self.max_drawdown_pct * fraction
            if drawdown_pct >= threshold and threshold not in self._fired_thresholds:
                self._fired_thresholds.add(threshold)
                alerts.append(f"drawdown_{int(fraction * 100)}pct_of_limit")
        if drawdown_pct >= self.max_drawdown_pct:
            self.paused = True
        if self.paused and drawdown_pct <= self.resume_pct:
            self.paused = False
            self._fired_thresholds.clear()
        return DrawdownStatus(
            equity=equity,
            peak_equity=self.peak_equity,
            drawdown=drawdown,
            drawdown_pct=drawdown_pct,
            paused=self.paused,
            alerts=tuple(alerts),
        )

    def can_trade(self, equity: float) -> bool:
        return not self.update(equity).paused
