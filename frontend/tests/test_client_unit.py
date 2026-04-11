from unittest.mock import MagicMock, patch
from urllib import error
import pytest
from frontend.python.client import FuelTrackerClient, FuelTrackerApiError

@pytest.fixture
def client():
    return FuelTrackerClient("http://fake-api")

@patch("urllib.request.build_opener")
def test_client_healthcheck_success(mock_build_opener, client):
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = b'{"status": "ok"}'
    
    mock_opener = MagicMock()
    mock_opener.open.return_value.__enter__.return_value = mock_resp
    client._opener = mock_opener

    res = client.healthcheck()
    assert res == {"status": "ok"}
    mock_opener.open.assert_called_once()
    req = mock_opener.open.call_args[0][0]
    assert req.full_url == "http://fake-api/api/health"

@patch("urllib.request.build_opener")
def test_client_healthcheck_http_error(mock_build_opener, client):
    mock_opener = MagicMock()
    mock_error = error.HTTPError("url", 500, "Error", hdrs={}, fp=None)
    mock_opener.open.side_effect = mock_error
    client._opener = mock_opener

    with pytest.raises(FuelTrackerApiError) as exc:
        client.healthcheck()
    
    assert exc.value.status_code == 500
    assert "API request failed" in str(exc.value)

@patch("urllib.request.build_opener")
def test_client_create_refueling(mock_build_opener, client):
    mock_resp = MagicMock()
    mock_resp.status = 201
    mock_resp.read.return_value = b'{"id": 42}'
    
    mock_opener = MagicMock()
    mock_opener.open.return_value.__enter__.return_value = mock_resp
    client._opener = mock_opener

    payload = {"liters": 40.0}
    res = client.create_refueling(payload, device_id="test_device")
    assert res == {"id": 42}
    
    req = mock_opener.open.call_args[0][0]
    assert req.method == "POST"
    assert req.headers.get("Content-type") == "application/json"
    assert req.headers.get("X-device-id") == "test_device"

@patch("urllib.request.build_opener")
def test_client_delete_refueling(mock_build_opener, client):
    mock_resp = MagicMock()
    mock_resp.status = 204
    mock_resp.read.return_value = b''
    
    mock_opener = MagicMock()
    mock_opener.open.return_value.__enter__.return_value = mock_resp
    client._opener = mock_opener

    client.delete_refueling(10, device_id="test_device")
    req = mock_opener.open.call_args[0][0]
    assert req.method == "DELETE"
    assert "api/refuelings/10" in req.full_url
