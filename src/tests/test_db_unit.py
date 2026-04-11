from __future__ import annotations

import sqlite3
from pathlib import Path

from fuel_tracker.db import Database


def test_database_initialize_creates_schema(tmp_path: Path) -> None:
    database_path = tmp_path / "nested" / "fuel.db"
    database = Database(database_path)

    database.initialize()

    assert database_path.exists()
    with sqlite3.connect(database_path) as connection:
        table = connection.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name = 'refuelings'
            """
        ).fetchone()
        index_row = connection.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'index' AND name = 'idx_refuelings_device_id'
            """
        ).fetchone()

    assert table == ("refuelings",)
    assert index_row == ("idx_refuelings_device_id",)


def test_database_connection_rolls_back_on_error(tmp_path: Path) -> None:
    database = Database(tmp_path / "fuel.db")
    database.initialize()

    try:
        with database.connection() as connection:
            connection.execute(
                """
                INSERT INTO refuelings (
                    device_id,
                    refueled_at,
                    odometer_km,
                    liters,
                    total_cost
                ) VALUES (?, ?, ?, ?, ?)
                """,
                ("device-1", "2026-04-01", 1000, 40, 2000),
            )
            raise RuntimeError("boom")
    except RuntimeError:
        pass

    with database.connection() as connection:
        row = connection.execute(
            "SELECT COUNT(*) FROM refuelings"
        ).fetchone()

    assert row[0] == 0
