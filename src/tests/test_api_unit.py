from __future__ import annotations

from unittest.mock import Mock

from fastapi import Response

from fuel_tracker.api import (
    DEVICE_ID_COOKIE_NAME,
    attach_device_cookie,
    resolve_device_id,
)


def test_resolve_device_id_prefers_header() -> None:
    service = Mock()

    result = resolve_device_id(
        service=service,
        device_id_header="header-id",
        device_id_cookie="cookie-id",
    )

    assert result == "header-id"
    service.generate_device_id.assert_not_called()


def test_resolve_device_id_uses_cookie_when_header_absent() -> None:
    service = Mock()

    result = resolve_device_id(
        service=service,
        device_id_header=None,
        device_id_cookie="cookie-id",
    )

    assert result == "cookie-id"
    service.generate_device_id.assert_not_called()


def test_resolve_device_id_generates_new_value_when_missing() -> None:
    service = Mock()
    service.generate_device_id.return_value = "generated-id"

    result = resolve_device_id(
        service=service,
        device_id_header=None,
        device_id_cookie=None,
    )

    assert result == "generated-id"
    service.generate_device_id.assert_called_once_with()


def test_attach_device_cookie_sets_expected_cookie_attributes() -> None:
    response = Response()

    attach_device_cookie(response, "device-a")

    cookie_header = response.headers["set-cookie"]
    assert DEVICE_ID_COOKIE_NAME in cookie_header
    assert "device-a" in cookie_header
    assert "HttpOnly" in cookie_header
    assert "SameSite=lax" in cookie_header
