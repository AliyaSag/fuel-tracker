from unittest.mock import MagicMock
from streamlit.testing.v1 import AppTest
from frontend.python.client import FuelTrackerClient


def test_frontend_integration_loads_and_displays_data():
    """Integration test checking Streamlit uses FuelTrackerClient."""
    mock_client = MagicMock(spec=FuelTrackerClient)

    mock_client.healthcheck.return_value = {"status": "ok"}
    mock_client.list_refuelings.return_value = [
        {
            "id": 100,
            "refueled_at": "2026-04-10T10:00:00",
            "odometer_km": 10000.0,
            "liters": 40.0,
            "total_cost": 2000.0,
            "distance_since_previous_km": 0.0,
            "consumption_l_per_100km": None,
            "fuel_type": "",
            "station_name": ""
        }
    ]
    mock_client.get_stats.return_value = {
        "total_entries": 1,
        "total_liters": 40.0,
        "total_cost": 2000.0,
        "total_distance_km": 0.0,
        "average_consumption_l_per_100km": None,
        "average_cost_per_km": None
    }
    mock_client.cookie_device_id = "test_device"

    # Set up the AppTest instance without running it
    at = AppTest.from_file("frontend/python/app.py")

    # Inject the mocked client into session state so `get_client` uses it
    at.session_state["api_client"] = mock_client
    at.session_state["api_base_url"] = "http://127.0.0.1:8000"

    # Run the streamit app
    at.run()

    assert not at.exception

    # Check title
    assert at.title[0].value == "Fuel Tracker"

    # Check stats are populated correctly
    metrics = at.metric
    # Looking at at.metric[0] for instance
    assert "Entries" in [m.label for m in metrics]

    # Check total cost is formatted correctly with RUB
    assert any("RUB" in str(m.value) for m in metrics)

    # Ensure tabs got rendered
    # Streamlit AppTest has a tabs property
    assert len(at.tabs) == 3
