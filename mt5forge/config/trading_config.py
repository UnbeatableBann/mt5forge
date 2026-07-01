"""Top-level trading configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from mt5forge.config.backtest_config import BacktestConfig
from mt5forge.config.notification_config import NotificationConfig
from mt5forge.config.risk_config import RiskConfig
from mt5forge.core.constants import Timeframe

if TYPE_CHECKING:
    from mt5forge.connection.connector import MT5Credentials


class MT5Config(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    terminal_path: str = ""
    account: int = 0
    password: str = ""
    server: str = ""
    reconnect_attempts: int = Field(default=20, ge=1)
    reconnect_delay_base: float = Field(default=2.0, gt=0.0)
    reconnect_delay_max: float = Field(default=30.0, gt=0.0)

    def credentials(self) -> MT5Credentials:
        from mt5forge.connection.connector import MT5Credentials

        return MT5Credentials(account=self.account, password=self.password, server=self.server)


class TradingRuntimeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    symbols: list[str] = Field(default_factory=lambda: ["EURUSD"])
    default_timeframe: Timeframe = Timeframe.H1
    magic_base: int = 10000
    conflict_policy: str = "ALLOW_BOTH"


class HedgeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    activation_loss_pips: float = Field(default=30.0, gt=0.0)
    max_hedge_layers: int = Field(default=3, ge=1)
    target_net_pnl: float = 0.0
    recovery_check_interval: int = Field(default=60, ge=1)
    max_duration_seconds: int = Field(default=86_400, ge=60)


class ConditionsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    trend_ma_fast: int = Field(default=21, ge=1)
    trend_ma_slow: int = Field(default=50, ge=1)
    trend_ma_long: int = Field(default=200, ge=1)
    atr_period: int = Field(default=14, ge=1)
    atr_multiplier_high_vol: float = Field(default=2.0, gt=0.0)
    spread_abnormal_multiplier: float = Field(default=5.0, gt=0.0)
    classification_interval: int = Field(default=300, ge=1)


class LoggingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    level: str = "INFO"
    log_dir: str = "logs"
    max_bytes: int = Field(default=10_485_760, ge=1)
    backup_count: int = Field(default=5, ge=1)
    json_logs: bool = True


class MonitoringConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    terminal_check_interval: int = Field(default=5, ge=1)
    broker_check_interval: int = Field(default=10, ge=1)
    internet_check_interval: int = Field(default=15, ge=1)
    heartbeat_interval: int = Field(default=30, ge=1)
    execution_latency_threshold_ms: float = Field(default=500.0, gt=0.0)
    cpu_alert_threshold: float = Field(default=80.0, ge=0.0, le=100.0)
    memory_alert_threshold: float = Field(default=80.0, ge=0.0, le=100.0)


class TradingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    mt5: MT5Config = Field(default_factory=MT5Config)
    trading: TradingRuntimeConfig = Field(default_factory=TradingRuntimeConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)
    hedge: HedgeConfig = Field(default_factory=HedgeConfig)
    conditions: ConditionsConfig = Field(default_factory=ConditionsConfig)
    backtest: BacktestConfig = Field(default_factory=BacktestConfig)
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
