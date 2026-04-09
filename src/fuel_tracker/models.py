"""Pydantic models for the API layer."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RefuelingCreate(BaseModel):
    """Incoming payload for creating a refueling record."""

    refueled_at: date
    odometer_km: float = Field(gt=0)
    liters: float = Field(gt=0)
    total_cost: Optional[float] = Field(default=None, gt=0)
    price_per_liter: Optional[float] = Field(default=None, gt=0)
    fuel_type: Optional[str] = Field(default=None, max_length=50)
    station_name: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_cost_fields(self) -> "RefuelingCreate":
        """Require either total cost or price per liter."""
        if self.total_cost is None and self.price_per_liter is None:
            raise ValueError(
                "Either total_cost or price_per_liter must be provided"
            )
        return self


class RefuelingRecord(BaseModel):
    """Stored refueling record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: str
    refueled_at: date
    odometer_km: float
    liters: float
    total_cost: float
    fuel_type: Optional[str]
    station_name: Optional[str]
    notes: Optional[str]
    created_at: datetime


class RefuelingHistoryItem(RefuelingRecord):
    """Refueling record extended with calculated metrics."""

    distance_since_previous_km: Optional[float] = None
    consumption_l_per_100km: Optional[float] = None


class FuelStats(BaseModel):
    """Aggregate dashboard metrics."""

    total_entries: int
    total_liters: float
    total_cost: float
    total_distance_km: float
    average_consumption_l_per_100km: Optional[float]
    average_cost_per_km: Optional[float]
