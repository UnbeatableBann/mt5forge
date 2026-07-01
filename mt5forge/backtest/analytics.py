"""Backtest performance analytics."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta

import pandas as pd

from mt5forge.backtest.simulator import SimulatedTrade


@dataclass(slots=True)
class BacktestResult:
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    net_profit: float
    gross_profit: float
    gross_loss: float
    profit_factor: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    max_drawdown_pct: float
    recovery_factor: float
    avg_trade_duration: timedelta
    avg_win: float
    avg_loss: float
    avg_rr_ratio: float
    largest_win: float
    largest_loss: float
    consecutive_wins_max: int
    consecutive_losses_max: int
    equity_curve: pd.Series
    drawdown_curve: pd.Series
    avg_signal_latency_ms: float
    total_backtest_duration_seconds: float


class ComparisonReport:
    """Compare multiple strategy backtest results."""

    def __init__(self, results: dict[str, BacktestResult]) -> None:
        self.results = results

    def ranked_by_profit_factor(self) -> list[tuple[str, BacktestResult]]:
        return sorted(self.results.items(), key=lambda item: item[1].profit_factor, reverse=True)


class PerformanceAnalytics:
    """Compute standard trading metrics from simulated trades and equity."""

    def compute(
        self,
        trades: list[SimulatedTrade],
        equity_points: list[tuple[datetime, float]],
        initial_balance: float,
        signal_latencies_ms: list[float],
        duration_seconds: float,
    ) -> BacktestResult:
        profits = [trade.profit for trade in trades]
        wins = [profit for profit in profits if profit > 0]
        losses = [profit for profit in profits if profit < 0]
        equity_curve = self._equity_series(equity_points, initial_balance)
        drawdown_curve = equity_curve.cummax() - equity_curve
        max_drawdown = float(drawdown_curve.max()) if not drawdown_curve.empty else 0.0
        peak = float(equity_curve.cummax().max()) if not equity_curve.empty else initial_balance
        max_drawdown_pct = max_drawdown / peak if peak > 0 else 0.0
        returns = equity_curve.pct_change().dropna()
        downside = returns[returns < 0]
        sharpe = self._ratio(returns.mean(), returns.std()) * math.sqrt(252) if not returns.empty else 0.0
        sortino = self._ratio(returns.mean(), downside.std()) * math.sqrt(252) if not downside.empty else 0.0
        net_profit = sum(profits)
        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        durations = [trade.closed_at - trade.opened_at for trade in trades]
        avg_duration = sum(durations, timedelta()) / len(durations) if durations else timedelta()
        return BacktestResult(
            total_trades=len(trades),
            winning_trades=len(wins),
            losing_trades=len(losses),
            win_rate=(len(wins) / len(trades)) if trades else 0.0,
            net_profit=net_profit,
            gross_profit=gross_profit,
            gross_loss=gross_loss,
            profit_factor=(gross_profit / gross_loss) if gross_loss > 0 else float("inf") if gross_profit > 0 else 0.0,
            sharpe_ratio=float(sharpe) if not math.isnan(float(sharpe)) else 0.0,
            sortino_ratio=float(sortino) if not math.isnan(float(sortino)) else 0.0,
            calmar_ratio=(net_profit / initial_balance / max_drawdown_pct) if max_drawdown_pct > 0 else 0.0,
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_drawdown_pct,
            recovery_factor=(net_profit / max_drawdown) if max_drawdown > 0 else 0.0,
            avg_trade_duration=avg_duration,
            avg_win=(sum(wins) / len(wins)) if wins else 0.0,
            avg_loss=(sum(losses) / len(losses)) if losses else 0.0,
            avg_rr_ratio=self._avg_rr(trades),
            largest_win=max(wins) if wins else 0.0,
            largest_loss=min(losses) if losses else 0.0,
            consecutive_wins_max=self._max_streak(profits, positive=True),
            consecutive_losses_max=self._max_streak(profits, positive=False),
            equity_curve=equity_curve,
            drawdown_curve=drawdown_curve,
            avg_signal_latency_ms=(sum(signal_latencies_ms) / len(signal_latencies_ms)) if signal_latencies_ms else 0.0,
            total_backtest_duration_seconds=duration_seconds,
        )

    @staticmethod
    def _equity_series(equity_points: list[tuple[datetime, float]], initial_balance: float) -> pd.Series:
        if not equity_points:
            return pd.Series([initial_balance])
        index = [item[0] for item in equity_points]
        values = [item[1] for item in equity_points]
        return pd.Series(values, index=pd.to_datetime(index))

    @staticmethod
    def _ratio(numerator: float, denominator: float) -> float:
        if denominator is None or float(denominator) == 0.0 or math.isnan(float(denominator)):
            return 0.0
        return float(numerator) / float(denominator)

    @staticmethod
    def _avg_rr(trades: list[SimulatedTrade]) -> float:
        ratios = []
        for trade in trades:
            risk = abs(trade.entry_price - trade.exit_price)
            reward = abs(trade.profit)
            if risk > 0:
                ratios.append(reward / risk)
        return sum(ratios) / len(ratios) if ratios else 0.0

    @staticmethod
    def _max_streak(values: list[float], positive: bool) -> int:
        best = 0
        current = 0
        for value in values:
            matched = value > 0 if positive else value < 0
            current = current + 1 if matched else 0
            best = max(best, current)
        return best
