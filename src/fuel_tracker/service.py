"""Business logic for refueling workflows and calculations."""

from __future__ import annotations

from dataclasses import dataclass
from secrets import token_urlsafe
from typing import Optional

from fastapi import HTTPException, status

from fuel_tracker.models import (
    FuelStats,
    RefuelingCreate,
    RefuelingHistoryItem,
    RefuelingRecord,
)
from fuel_tracker.repository import RefuelingRepository


@dataclass
class RefuelingService:
    """Application service for refueling operations."""

    repository: RefuelingRepository

    def create_refueling(
        self,
        device_id: str,
        payload: RefuelingCreate,
    ) -> RefuelingRecord:
        """Validate and store a refueling record."""
        latest_odometer = self.repository.get_latest_odometer(device_id)
        if (
            latest_odometer is not None
            and payload.odometer_km <= latest_odometer
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "odometer_km must be greater than the latest saved value"
                ),
            )
        total_cost = self._resolve_total_cost(payload)
        return self.repository.create(device_id, payload, total_cost)

    def list_history(self, device_id: str) -> list[RefuelingHistoryItem]:
        """List all refuelings enriched with consumption metrics."""
        records = self.repository.list_all(device_id)
        history: list[RefuelingHistoryItem] = []

        previous: Optional[RefuelingRecord] = None
        for record in records:
            distance = None
            consumption = None
            if previous is not None:
                distance_delta = record.odometer_km - previous.odometer_km
                distance = round(distance_delta, 2)
                if distance_delta > 0:
                    consumption = round(
                        (record.liters / distance_delta) * 100,
                        2,
                    )

            history.append(
                RefuelingHistoryItem(
                    **record.model_dump(),
                    distance_since_previous_km=distance,
                    consumption_l_per_100km=consumption,
                )
            )
            previous = record
        return history

    def get_refueling(self, device_id: str, record_id: int) -> RefuelingRecord:
        """Return a single refueling or raise 404."""
        record = self.repository.get(device_id, record_id)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Refueling record not found",
            )
        return record

    def delete_refueling(self, device_id: str, record_id: int) -> None:
        """Delete a refueling or raise 404."""
        deleted = self.repository.delete(device_id, record_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Refueling record not found",
            )

    def get_stats(self, device_id: str) -> FuelStats:
        """Calculate aggregate dashboard metrics."""
        history = self.list_history(device_id)
        total_entries = len(history)
        total_liters = round(sum(item.liters for item in history), 2)
        total_cost = round(sum(item.total_cost for item in history), 2)
        total_distance = self._calculate_total_distance(history)
        liters_for_consumption = self._calculate_liters_for_consumption(
            history
        )
        average_consumption = self._calculate_average_consumption(
            liters_for_consumption,
            total_distance,
        )
        average_cost_per_km = self._calculate_average_cost_per_km(
            total_cost,
            total_distance,
        )

        return FuelStats(
            total_entries=total_entries,
            total_liters=total_liters,
            total_cost=total_cost,
            total_distance_km=total_distance,
            average_consumption_l_per_100km=average_consumption,
            average_cost_per_km=average_cost_per_km,
        )

    @staticmethod
    def _resolve_total_cost(payload: RefuelingCreate) -> float:
        if payload.total_cost is not None:
            return round(payload.total_cost, 2)
        if payload.price_per_liter is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="price_per_liter is required when total_cost is absent",
            )
        return round(payload.liters * payload.price_per_liter, 2)

    @staticmethod
    def _calculate_total_distance(
        history: list[RefuelingHistoryItem],
    ) -> float:
        return round(
            sum(item.distance_since_previous_km or 0 for item in history),
            2,
        )

    @staticmethod
    def _calculate_liters_for_consumption(
        history: list[RefuelingHistoryItem],
    ) -> float:
        return round(
            sum(
                item.liters
                for item in history
                if item.distance_since_previous_km is not None
                and item.distance_since_previous_km > 0
            ),
            2,
        )

    @staticmethod
    def _calculate_average_consumption(
        liters_for_consumption: float,
        total_distance: float,
    ) -> Optional[float]:
        if total_distance <= 0:
            return None
        return round((liters_for_consumption / total_distance) * 100, 2)

    @staticmethod
    def _calculate_average_cost_per_km(
        total_cost: float,
        total_distance: float,
    ) -> Optional[float]:
        if total_distance <= 0:
            return None
        return round(total_cost / total_distance, 2)

    @staticmethod
    def generate_device_id() -> str:
        """Generate a lightweight per-device identifier."""
        return token_urlsafe(24)
