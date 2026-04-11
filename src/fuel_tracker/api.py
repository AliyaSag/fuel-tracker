"""FastAPI route definitions."""

from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, Header, Response, status

from fuel_tracker.models import (
    FuelStats,
    RefuelingCreate,
    RefuelingHistoryItem,
    RefuelingRecord,
)
from fuel_tracker.service import RefuelingService


DEVICE_ID_COOKIE_NAME = "fuel_tracker_device_id"
DEVICE_ID_HEADER_NAME = "X-Device-Id"


def build_api_router() -> APIRouter:
    """Create the application API router."""
    router = APIRouter(prefix="/api")

    @router.get("/health", tags=["system"])
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @router.post(
        "/refuelings",
        response_model=RefuelingRecord,
        status_code=status.HTTP_201_CREATED,
        tags=["refuelings"],
    )
    def create_refueling(
        payload: RefuelingCreate,
        response: Response,
        device_id: str = Depends(resolve_device_id),
        service: RefuelingService = Depends(get_service),
    ) -> RefuelingRecord:
        attach_device_cookie(response, device_id)
        return service.create_refueling(device_id, payload)

    @router.get(
        "/refuelings",
        response_model=list[RefuelingHistoryItem],
        tags=["refuelings"],
    )
    def list_refuelings(
        response: Response,
        device_id: str = Depends(resolve_device_id),
        service: RefuelingService = Depends(get_service),
    ) -> list[RefuelingHistoryItem]:
        attach_device_cookie(response, device_id)
        return service.list_history(device_id)

    @router.get(
        "/refuelings/{record_id}",
        response_model=RefuelingRecord,
        tags=["refuelings"],
    )
    def get_refueling(
        record_id: int,
        response: Response,
        device_id: str = Depends(resolve_device_id),
        service: RefuelingService = Depends(get_service),
    ) -> RefuelingRecord:
        attach_device_cookie(response, device_id)
        return service.get_refueling(device_id, record_id)

    @router.delete(
        "/refuelings/{record_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        tags=["refuelings"],
    )
    def delete_refueling(
        record_id: int,
        response: Response,
        device_id: str = Depends(resolve_device_id),
        service: RefuelingService = Depends(get_service),
    ) -> Response:
        service.delete_refueling(device_id, record_id)
        attach_device_cookie(response, device_id)
        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    @router.get("/stats", response_model=FuelStats, tags=["stats"])
    def get_stats(
        response: Response,
        device_id: str = Depends(resolve_device_id),
        service: RefuelingService = Depends(get_service),
    ) -> FuelStats:
        attach_device_cookie(response, device_id)
        return service.get_stats(device_id)

    return router


def get_service() -> RefuelingService:
    """Resolve service instance from the application state."""
    raise RuntimeError("Dependency override is not configured")


def resolve_device_id(
    service: RefuelingService = Depends(get_service),
    device_id_header: str | None = Header(
        default=None,
        alias=DEVICE_ID_HEADER_NAME,
    ),
    device_id_cookie: str | None = Cookie(
        default=None,
        alias=DEVICE_ID_COOKIE_NAME,
    ),
) -> str:
    """Resolve device identity from header or cookie."""
    if device_id_header:
        return device_id_header
    if device_id_cookie:
        return device_id_cookie
    return service.generate_device_id()


def attach_device_cookie(response: Response, device_id: str) -> None:
    """Persist resolved device identity on the client."""
    response.set_cookie(
        key=DEVICE_ID_COOKIE_NAME,
        value=device_id,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 24 * 365,
    )
