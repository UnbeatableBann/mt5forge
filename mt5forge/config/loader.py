"""TOML and environment configuration loading."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from mt5forge.config.trading_config import TradingConfig
from mt5forge.core.exceptions import ConfigurationError


class ConfigLoader:
    """Load and validate MT5Forge configuration."""

    ENV_PREFIX = "MT5FORGE_"

    @classmethod
    def from_toml(cls, path: str | Path) -> TradingConfig:
        config_path = Path(path)
        if not config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")
        try:
            with config_path.open("rb") as handle:
                data = tomllib.load(handle)
        except OSError as exc:
            raise ConfigurationError(f"Could not read configuration: {exc}") from exc
        return cls.from_mapping(data)

    @classmethod
    def from_env(cls, prefix: str | None = None) -> TradingConfig:
        env_prefix = prefix or cls.ENV_PREFIX
        data: dict[str, Any] = {}
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                cls._assign_env_value(data, key.removeprefix(env_prefix).lower().split("_"), value)
        return cls.from_mapping(data)

    @classmethod
    def load(cls, path: str | Path | None = None) -> TradingConfig:
        file_data: dict[str, Any] = {}
        if path:
            config_path = Path(path)
            if config_path.exists():
                with config_path.open("rb") as handle:
                    file_data = tomllib.load(handle)
        env_config = cls.from_env()
        merged = cls._deep_merge(file_data, env_config.model_dump(exclude_defaults=True))
        return cls.from_mapping(merged)

    @staticmethod
    def from_mapping(data: dict[str, Any]) -> TradingConfig:
        try:
            return TradingConfig.model_validate(data)
        except ValidationError as exc:
            raise ConfigurationError(str(exc)) from exc

    @staticmethod
    def _assign_env_value(data: dict[str, Any], parts: list[str], value: str) -> None:
        if not parts:
            return_value = value
            data["_"] = return_value
            return
        cursor: dict[str, Any] = data
        for part in parts[:-1]:
            next_value = cursor.setdefault(part, {})
            if not isinstance(next_value, dict):
                next_value = {}
                cursor[part] = next_value
            cursor = next_value
        cursor[parts[-1]] = ConfigLoader._coerce(value)

    @staticmethod
    def _coerce(value: str) -> Any:
        lowered = value.strip().lower()
        if lowered in {"true", "false"}:
            return lowered == "true"
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                if "," in value:
                    return [item.strip() for item in value.split(",") if item.strip()]
                return value

    @staticmethod
    def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        merged = dict(base)
        for key, value in override.items():
            existing = merged.get(key)
            if isinstance(existing, dict) and isinstance(value, dict):
                merged[key] = ConfigLoader._deep_merge(existing, value)
            else:
                merged[key] = value
        return merged
