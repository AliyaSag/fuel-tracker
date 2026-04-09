"""SQLite integration primitives."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


SCHEMA = """
CREATE TABLE IF NOT EXISTS refuelings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    refueled_at TEXT NOT NULL,
    odometer_km REAL NOT NULL,
    liters REAL NOT NULL,
    total_cost REAL NOT NULL,
    fuel_type TEXT,
    station_name TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_refuelings_device_id
ON refuelings(device_id);
"""


class Database:
    """Very small SQLite wrapper with safe defaults."""

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        print(f"Using database at {self._database_path.absolute()}")

    @property
    def database_path(self) -> Path:
        """Return configured SQLite database path."""
        return self._database_path

    def initialize(self) -> None:
        """Create DB directories and tables when missing."""
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as connection:
            connection.executescript(SCHEMA)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Open a SQLite connection with row access by column name."""
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
