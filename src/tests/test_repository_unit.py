from __future__ import annotations

from datetime import date
from pathlib import Path

from fuel_tracker.db import Database
from fuel_tracker.models import RefuelingCreate
from fuel_tracker.repository import RefuelingRepository


def make_repository(tmp_path: Path) -> RefuelingRepository:
    database = Database(tmp_path / "repo.db")
    database.initialize()
    return RefuelingRepository(database)


def build_payload(
    *,
    refueled_at: str,
    odometer_km: float,
    liters: float,
    total_cost: float,
) -> RefuelingCreate:
    return RefuelingCreate(
        refueled_at=refueled_at,
        odometer_km=odometer_km,
        liters=liters,
        total_cost=total_cost,
    )


def test_repository_crud_is_scoped_by_device_id(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    first = repository.create(
        "device-a",
        build_payload(
            refueled_at="2026-04-01",
            odometer_km=10000,
            liters=40,
            total_cost=2000,
        ),
        2000,
    )
    repository.create(
        "device-b",
        build_payload(
            refueled_at="2026-04-02",
            odometer_km=8000,
            liters=20,
            total_cost=900,
        ),
        900,
    )

    listed = repository.list_all("device-a")
    loaded = repository.get("device-a", first.id)
    deleted = repository.delete("device-a", first.id)
    after_delete = repository.get("device-a", first.id)

    assert len(listed) == 1
    assert listed[0].device_id == "device-a"
    assert loaded is not None
    assert loaded.refueled_at == date(2026, 4, 1)
    assert deleted is True
    assert after_delete is None
    assert repository.list_all("device-b")[0].device_id == "device-b"


def test_repository_get_latest_odometer_isolated_by_device(
    tmp_path: Path,
) -> None:
    repository = make_repository(tmp_path)
    repository.create(
        "device-a",
        build_payload(
            refueled_at="2026-04-01",
            odometer_km=10000,
            liters=30,
            total_cost=1500,
        ),
        1500,
    )
    repository.create(
        "device-a",
        build_payload(
            refueled_at="2026-04-03",
            odometer_km=10450,
            liters=28,
            total_cost=1456,
        ),
        1456,
    )
    repository.create(
        "device-b",
        build_payload(
            refueled_at="2026-04-02",
            odometer_km=7000,
            liters=22,
            total_cost=1100,
        ),
        1100,
    )

    assert repository.get_latest_odometer("device-a") == 10450
    assert repository.get_latest_odometer("device-b") == 7000
    assert repository.get_latest_odometer("missing-device") is None
