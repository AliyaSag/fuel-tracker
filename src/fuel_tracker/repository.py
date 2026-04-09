"""Persistence layer for refueling records."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from fuel_tracker.db import Database
from fuel_tracker.models import RefuelingCreate, RefuelingRecord


@dataclass(frozen=True)
class StoredRefueling:
    """Internal representation of a stored refueling row."""

    id: int
    device_id: str
    refueled_at: date
    odometer_km: float
    liters: float
    total_cost: float
    fuel_type: Optional[str]
    station_name: Optional[str]
    notes: Optional[str]
    created_at: datetime

    def to_model(self) -> RefuelingRecord:
        """Convert storage object to API model."""
        return RefuelingRecord.model_validate(self)


class RefuelingRepository:
    """Repository for CRUD operations on refuelings."""

    def __init__(self, database: Database) -> None:
        self._database = database

    def create(
        self,
        device_id: str,
        payload: RefuelingCreate,
        total_cost: float,
    ) -> RefuelingRecord:
        """Insert a new refueling row and return it."""
        query = """
        INSERT INTO refuelings (
            device_id,
            refueled_at,
            odometer_km,
            liters,
            total_cost,
            fuel_type,
            station_name,
            notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        values = (
            device_id,
            payload.refueled_at.isoformat(),
            payload.odometer_km,
            payload.liters,
            total_cost,
            payload.fuel_type,
            payload.station_name,
            payload.notes,
        )
        with self._database.connection() as connection:
            cursor = connection.execute(query, values)
            row = connection.execute(
                "SELECT * FROM refuelings WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
        return self._row_to_model(row)

    def list_all(self, device_id: str) -> list[RefuelingRecord]:
        """Return all refueling rows in odometer order."""
        with self._database.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM refuelings
                WHERE device_id = ?
                ORDER BY odometer_km ASC, refueled_at ASC, id ASC
                """,
                (device_id,),
            ).fetchall()
        return [self._row_to_model(row) for row in rows]

    def get(self, device_id: str, record_id: int) -> Optional[RefuelingRecord]:
        """Return a single refueling row when it exists."""
        with self._database.connection() as connection:
            row = connection.execute(
                """
                SELECT * FROM refuelings
                WHERE device_id = ? AND id = ?
                """,
                (device_id, record_id),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_model(row)

    def delete(self, device_id: str, record_id: int) -> bool:
        """Delete a refueling row by id."""
        with self._database.connection() as connection:
            cursor = connection.execute(
                """
                DELETE FROM refuelings
                WHERE device_id = ? AND id = ?
                """,
                (device_id, record_id),
            )
        return cursor.rowcount > 0

    def get_latest_odometer(self, device_id: str) -> Optional[float]:
        """Return the largest odometer value currently stored."""
        with self._database.connection() as connection:
            row = connection.execute(
                """
                SELECT MAX(odometer_km) AS max_odometer
                FROM refuelings
                WHERE device_id = ?
                """,
                (device_id,),
            ).fetchone()
        if row is None or row["max_odometer"] is None:
            return None
        return row["max_odometer"]

    @staticmethod
    def _row_to_model(row: sqlite3.Row) -> RefuelingRecord:
        stored = StoredRefueling(
            id=row["id"],
            device_id=row["device_id"],
            refueled_at=date.fromisoformat(row["refueled_at"]),
            odometer_km=row["odometer_km"],
            liters=row["liters"],
            total_cost=row["total_cost"],
            fuel_type=row["fuel_type"],
            station_name=row["station_name"],
            notes=row["notes"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        return stored.to_model()
