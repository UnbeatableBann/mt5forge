"""Built-in notification channels."""

from mt5forge.notifications.channels.console import ConsoleChannel
from mt5forge.notifications.channels.discord import DiscordChannel
from mt5forge.notifications.channels.email_channel import EmailChannel
from mt5forge.notifications.channels.file_channel import FileChannel
from mt5forge.notifications.channels.slack import SlackChannel
from mt5forge.notifications.channels.telegram import TelegramChannel
from mt5forge.notifications.channels.webhook import WebhookChannel

__all__ = [
    "ConsoleChannel",
    "DiscordChannel",
    "EmailChannel",
    "FileChannel",
    "SlackChannel",
    "TelegramChannel",
    "WebhookChannel",
]
