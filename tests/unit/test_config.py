"""Unit tests for application settings."""

from __future__ import annotations

import pytest

import industrial_ai
from industrial_ai.config import Settings, get_settings


def test_package_version() -> None:
    assert industrial_ai.__version__ == "0.1.0"


def test_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APP_NAME", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)

    settings = get_settings()

    assert settings.app_name == "industrial-ai-engineer"
    assert settings.environment == "development"
    assert settings.log_level == "INFO"
    assert settings.debug is False


def test_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_NAME", "test-app")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    monkeypatch.setenv("DEBUG", "true")

    settings = Settings.from_env()

    assert settings.app_name == "test-app"
    assert settings.environment == "test"
    assert settings.log_level == "DEBUG"
    assert settings.debug is True
    assert settings == get_settings()
