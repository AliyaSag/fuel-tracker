"""HTTP client for the Fuel Tracker backend API."""

from __future__ import annotations

import json
from http.cookiejar import CookieJar
from typing import Any
from urllib import error, request


DEVICE_ID_COOKIE_NAME = "fuel_tracker_device_id"
DEVICE_ID_HEADER_NAME = "X-Device-Id"


class FuelTrackerApiError(RuntimeError):
    """Raised when the frontend cannot complete an API request."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code


class FuelTrackerClient:
    """Stateful API client that keeps cookies between requests."""

    def __init__(self, base_url: str, timeout_seconds: float = 10.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._cookie_jar: CookieJar = CookieJar()
        self._opener = request.build_opener(
            request.HTTPCookieProcessor(self._cookie_jar)
        )

    @property
    def cookie_device_id(self) -> str | None:
        """Return current device id from API cookie if present."""
        for cookie in self._cookie_jar:
            if cookie.name == DEVICE_ID_COOKIE_NAME:
                return cookie.value
        return None

    def healthcheck(self) -> dict[str, Any]:
        response = self._request_json("GET", "/api/health")
        if isinstance(response, dict):
            return response
        return {"status": "unknown"}

    def list_refuelings(
        self,
        *,
        device_id: str | None = None,
    ) -> list[dict[str, Any]]:
        response = self._request_json(
            "GET",
            "/api/refuelings",
            device_id=device_id,
        )
        if isinstance(response, list):
            return response
        return []

    def get_stats(
        self,
        *,
        device_id: str | None = None,
    ) -> dict[str, Any]:
        response = self._request_json(
            "GET",
            "/api/stats",
            device_id=device_id,
        )
        if isinstance(response, dict):
            return response
        return {}

    def create_refueling(
        self,
        payload: dict[str, Any],
        *,
        device_id: str | None = None,
    ) -> dict[str, Any]:
        response = self._request_json(
            "POST",
            "/api/refuelings",
            payload=payload,
            device_id=device_id,
        )
        if isinstance(response, dict):
            return response
        raise FuelTrackerApiError("Unexpected API response for create request")

    def delete_refueling(
        self,
        record_id: int,
        *,
        device_id: str | None = None,
    ) -> None:
        self._request_json(
            "DELETE",
            f"/api/refuelings/{record_id}",
            device_id=device_id,
        )

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        device_id: str | None = None,
    ) -> Any:
        body = None
        headers: dict[str, str] = {"Accept": "application/json"}

        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        if device_id:
            headers[DEVICE_ID_HEADER_NAME] = device_id

        req = request.Request(
            url=f"{self._base_url}{path}",
            data=body,
            headers=headers,
            method=method,
        )

        try:
            with self._opener.open(req, timeout=self._timeout_seconds) as resp:
                content = resp.read()
                if resp.status == 204 or not content:
                    return None
                return json.loads(content.decode("utf-8"))
        except error.HTTPError as exc:
            message = self._extract_error_message(exc)
            raise FuelTrackerApiError(
                message,
                status_code=exc.code,
            ) from exc
        except error.URLError as exc:
            raise FuelTrackerApiError(
                (
                    "Cannot connect to backend API. "
                    "Check the URL and ensure FastAPI is running."
                )
            ) from exc

    @staticmethod
    def _extract_error_message(exc: error.HTTPError) -> str:
        fallback = f"API request failed with status {exc.code}"
        try:
            content = exc.read()
            if not content:
                return fallback
            data = json.loads(content.decode("utf-8"))
            detail = data.get("detail")
            if isinstance(detail, str) and detail.strip():
                return detail
            return fallback
        except Exception:
            return fallback
