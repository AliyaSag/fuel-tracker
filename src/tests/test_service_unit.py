from __future__ import annotations

from datetime import date, datetime
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from fuel_tracker.models import RefuelingCreate, RefuelingRecord
from fuel_tracker.service import RefuelingService


def build_record(
    *,
    record_id: int,
    device_id: str = "device-a",
    refueled_at: date = date(2026, 4, 1),
    odometer_km: float = 10000,
    liters: float = 40,
    total_cost: float = 2000,
) -> RefuelingRecord:
    return RefuelingRecord(
        id=record_id,
        device_id=device_id,
        refueled_at=refueled_at,
        odometer_km=odometer_km,
        liters=liters,
        total_cost=total_cost,
        fuel_type=None,
        station_name=None,
        notes=None,
        created_at=datetime(2026, 4, 1, 10, 0, 0),
    )


def build_payload(**overrides) -> RefuelingCreate:
    payload = {
        "refueled_at": "2026-04-01",
        "odometer_km": 10000,
        "liters": 40,
        "total_cost": 2000,
    }
    payload.update(overrides)
    return RefuelingCreate(**payload)


def test_create_refueling_uses_price_per_liter_when_total_missing() -> None:
    repository = Mock()
    repository.get_latest_odometer.return_value = None
    expected = build_record(record_id=1, total_cost=2200)
    repository.create.return_value = expected
    service = RefuelingService(repository)

    result = service.create_refueling(
        "device-a",
        build_payload(total_cost=None, price_per_liter=55),
    )

    assert result == expected
    repository.create.assert_called_once()
    _, payload, resolved_total_cost = repository.create.call_args.args
    assert resolved_total_cost == 2200
    assert payload.price_per_liter == 55


def test_create_refueling_rejects_non_increasing_odometer() -> None:
    repository = Mock()
    repository.get_latest_odometer.return_value = 10000
    service = RefuelingService(repository)

    with pytest.raises(HTTPException) as error:
        service.create_refueling("device-a", build_payload(odometer_km=9999))

    assert error.value.status_code == 400
    repository.create.assert_not_called()


def test_list_history_calculates_distances_and_consumption() -> None:
    repository = Mock()
    repository.list_all.return_value = [
        build_record(record_id=1, odometer_km=10000, liters=30),
        build_record(
            record_id=2,
            refueled_at=date(2026, 4, 5),
            odometer_km=10500,
            liters=35,
            total_cost=1925,
        ),
    ]
    service = RefuelingService(repository)

    history = service.list_history("device-a")

    assert history[0].distance_since_previous_km is None
    assert history[1].distance_since_previous_km == 500
    assert history[1].consumption_l_per_100km == 7.0


def test_get_refueling_returns_404_when_missing() -> None:
    repository = Mock()
    repository.get.return_value = None
    service = RefuelingService(repository)

    with pytest.raises(HTTPException) as error:
        service.get_refueling("device-a", 1)

    assert error.value.status_code == 404


def test_delete_refueling_returns_404_when_missing() -> None:
    repository = Mock()
    repository.delete.return_value = False
    service = RefuelingService(repository)

    with pytest.raises(HTTPException) as error:
        service.delete_refueling("device-a", 1)

    assert error.value.status_code == 404


def test_get_stats_returns_none_averages_without_distance() -> None:
    repository = Mock()
    repository.list_all.return_value = [build_record(record_id=1, liters=30)]
    service = RefuelingService(repository)

    stats = service.get_stats("device-a")

    assert stats.total_entries == 1
    assert stats.total_distance_km == 0
    assert stats.average_consumption_l_per_100km is None
    assert stats.average_cost_per_km is None


def test_generate_device_id_returns_non_empty_token() -> None:
    generated = RefuelingService.generate_device_id()

    assert isinstance(generated, str)
    assert len(generated) >= 16
