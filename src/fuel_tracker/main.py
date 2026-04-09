"""Application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from fuel_tracker.api import build_api_router, get_service
from fuel_tracker.config import Settings, get_settings
from fuel_tracker.db import Database
from fuel_tracker.repository import RefuelingRepository
from fuel_tracker.service import RefuelingService


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    resolved_settings = settings or get_settings()
    database = Database(resolved_settings.database_path)
    repository = RefuelingRepository(database)
    service = RefuelingService(repository)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
        database.initialize()
        yield

    app = FastAPI(
        title="Fuel Tracker API",
        description="Backend API for managing vehicle refueling history.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.dependency_overrides[get_service] = lambda: service
    app.include_router(build_api_router())
    return app


app = create_app()
