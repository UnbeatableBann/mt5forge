"""Notification channel configuration models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ChannelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    enabled: bool = False
    min_severity: str = "INFO"


class TelegramConfig(ChannelConfig):
    bot_token: str = ""
    chat_id: str = ""
    enabled: bool = False


class DiscordConfig(ChannelConfig):
    webhook_url: str = ""
    enabled: bool = False


class SlackConfig(ChannelConfig):
    webhook_url: str = ""
    enabled: bool = False


class WebhookConfig(ChannelConfig):
    url: str = ""
    headers: dict[str, str] = Field(default_factory=dict)
    enabled: bool = False


class EmailConfig(ChannelConfig):
    smtp_host: str = ""
    smtp_port: int = Field(default=587, ge=1, le=65535)
    username: str = ""
    password: str = ""
    from_address: str = ""
    to_address: str = ""
    use_tls: bool = True
    enabled: bool = False


class ConsoleConfig(ChannelConfig):
    enabled: bool = True


class FileConfig(ChannelConfig):
    enabled: bool = True
    path: str = "logs/alerts.jsonl"


class NotificationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    enabled: bool = True
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    discord: DiscordConfig = Field(default_factory=DiscordConfig)
    email: EmailConfig = Field(default_factory=EmailConfig)
    slack: SlackConfig = Field(default_factory=SlackConfig)
    webhook: WebhookConfig = Field(default_factory=WebhookConfig)
    console: ConsoleConfig = Field(default_factory=ConsoleConfig)
    file: FileConfig = Field(default_factory=FileConfig)
    rate_limits: dict[str, int] = Field(
        default_factory=lambda: {
            "mt5_disconnected": 60,
            "drawdown_warning": 300,
            "abnormal_spread": 30,
        }
    )
