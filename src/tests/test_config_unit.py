from __future__ import annotations

from pathlib import Path

from fuel_tracker.config import get_settings


def test_get_settings_uses_default_path(monkeypatch) -> None:
    monkeypatch.delenv("FUEL_TRACKER_DB_PATH", raising=False)

    settings = get_settings()

    assert settings.database_path == Path("fuel_tracker.db")


def test_get_settings_uses_environment_override(monkeypatch) -> None:
    monkeypatch.setenv("FUEL_TRACKER_DB_PATH", "data/custom.db")

    settings = get_settings()

    assert settings.database_path == Path("data/custom.db")
