"""Application settings loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    """Typed runtime configuration for the industrial AI platform."""

    app_name: str
    environment: str
    log_level: str
    debug: bool

    @classmethod
    def from_env(cls) -> Settings:
        """Build settings from process environment variables."""
        return cls(
            app_name=os.getenv("APP_NAME", "industrial-ai-engineer"),
            environment=os.getenv("ENVIRONMENT", "development"),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            debug=_env_bool("DEBUG", default=False),
        )


def get_settings() -> Settings:
    """Return settings loaded from the current environment."""
    return Settings.from_env()
