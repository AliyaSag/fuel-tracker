"""Application configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the application."""

    database_path: Path


def get_settings() -> Settings:
    """Build settings from environment variables."""
    raw_path = os.getenv("FUEL_TRACKER_DB_PATH", "fuel_tracker.db")
    return Settings(database_path=Path(raw_path))
