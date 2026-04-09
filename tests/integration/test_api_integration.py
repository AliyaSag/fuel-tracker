from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from fuel_tracker.config import Settings
from fuel_tracker.main import create_app


DEVICE_ID_COOKIE_NAME = "fuel_tracker_device_id"
DEVICE_ID_HEADER_NAME = "X-Device-Id"


def make_client(tmp_path: Path) -> TestClient:
    app = create_app(Settings(database_path=tmp_path / "test.db"))
    return TestClient(app)


def test_healthcheck(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert DEVICE_ID_COOKIE_NAME not in response.cookies


def test_create_and_list_refuelings_with_calculated_metrics(
    tmp_path: Path,
) -> None:
    with make_client(tmp_path) as client:
        first_response = client.post(
            "/api/refuelings",
            json={
                "refueled_at": "2026-04-01",
                "odometer_km": 10000,
                "liters": 40,
                "total_cost": 2000,
            },
        )
        device_cookie = first_response.cookies.get(DEVICE_ID_COOKIE_NAME)
        second_response = client.post(
            "/api/refuelings",
            json={
                "refueled_at": "2026-04-05",
                "odometer_km": 10500,
                "liters": 35,
                "price_per_liter": 55,
                "station_name": "Shell",
            },
        )
        history_response = client.get("/api/refuelings")

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert device_cookie is not None
    assert first_response.json()["device_id"] == device_cookie
    assert second_response.json()["device_id"] == device_cookie
    history = history_response.json()
    assert history_response.status_code == 200
    assert len(history) == 2
    assert history[0]["consumption_l_per_100km"] is None
    assert history[1]["distance_since_previous_km"] == 500.0
    assert history[1]["consumption_l_per_100km"] == 7.0
    assert history[1]["total_cost"] == 1925.0


def test_stats_endpoint_returns_aggregates(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        client.post(
            "/api/refuelings",
            json={
                "refueled_at": "2026-04-01",
                "odometer_km": 10000,
                "liters": 30,
                "total_cost": 1500,
            },
        )
        client.post(
            "/api/refuelings",
            json={
                "refueled_at": "2026-04-03",
                "odometer_km": 10400,
                "liters": 28,
                "total_cost": 1456,
            },
        )
        response = client.get("/api/stats")

    assert response.status_code == 200
    assert response.json() == {
        "total_entries": 2,
        "total_liters": 58.0,
        "total_cost": 2956.0,
        "total_distance_km": 400.0,
        "average_consumption_l_per_100km": 7.0,
        "average_cost_per_km": 7.39,
    }


def test_header_identity_keeps_data_isolated(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        first_response = client.post(
            "/api/refuelings",
            headers={DEVICE_ID_HEADER_NAME: "device-a"},
            json={
                "refueled_at": "2026-04-01",
                "odometer_km": 10000,
                "liters": 30,
                "total_cost": 1500,
            },
        )
        second_response = client.post(
            "/api/refuelings",
            headers={DEVICE_ID_HEADER_NAME: "device-b"},
            json={
                "refueled_at": "2026-04-02",
                "odometer_km": 8000,
                "liters": 20,
                "total_cost": 900,
            },
        )
        first_history = client.get(
            "/api/refuelings",
            headers={DEVICE_ID_HEADER_NAME: "device-a"},
        )
        second_history = client.get(
            "/api/refuelings",
            headers={DEVICE_ID_HEADER_NAME: "device-b"},
        )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert len(first_history.json()) == 1
    assert len(second_history.json()) == 1
    assert first_history.json()[0]["device_id"] == "device-a"
    assert second_history.json()[0]["device_id"] == "device-b"


def test_request_without_identity_receives_new_cookie(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.get("/api/refuelings")

    device_cookie = response.cookies.get(DEVICE_ID_COOKIE_NAME)
    assert response.status_code == 200
    assert response.json() == []
    assert device_cookie is not None
    assert len(device_cookie) >= 16


def test_create_rejects_non_increasing_odometer(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        client.post(
            "/api/refuelings",
            json={
                "refueled_at": "2026-04-01",
                "odometer_km": 10000,
                "liters": 30,
                "total_cost": 1500,
            },
        )
        response = client.post(
            "/api/refuelings",
            json={
                "refueled_at": "2026-04-02",
                "odometer_km": 9999,
                "liters": 20,
                "total_cost": 1000,
            },
        )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "odometer_km must be greater than the latest saved value"
    )


def test_delete_refueling(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        created = client.post(
            "/api/refuelings",
            json={
                "refueled_at": "2026-04-01",
                "odometer_km": 10000,
                "liters": 30,
                "total_cost": 1500,
            },
        )
        record_id = created.json()["id"]
        delete_response = client.delete(f"/api/refuelings/{record_id}")
        list_response = client.get("/api/refuelings")

    assert delete_response.status_code == 204
    assert list_response.json() == []
