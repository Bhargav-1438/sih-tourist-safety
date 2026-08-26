"""Pydantic schemas for patrol-location optimization (Prompt 6)."""
import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.risk import RiskLevel


class PatrolUnit(BaseModel):
    """A recommended patrol location and the risk zones it serves."""

    unit_id: int = Field(..., ge=1, description="1-based placement order")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    covers_zone_ids: list[int] = Field(..., min_length=1)
    covered_zone_count: int = Field(..., ge=1)
    covered_weight: int = Field(..., ge=0, description="Sum of served zones' risk_score")
    coverage_share_pct: float = Field(..., ge=0, le=100)
    avg_zone_distance_km: float = Field(..., ge=0)
    highest_risk_level: RiskLevel


class UncoveredZone(BaseModel):
    """A risk zone not served by any patrol (explicit gap reporting)."""

    zone_id: int = Field(..., ge=1)
    risk_score: int = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    center_latitude: float = Field(..., ge=-90, le=90)
    center_longitude: float = Field(..., ge=-180, le=180)


class PatrolPlanResponse(BaseModel):
    """Envelope returned by GET /api/patrol-plan."""

    generated_at: datetime.datetime
    algorithm: Literal["greedy_pmedian_weighted_coverage"]
    requested_units: int = Field(..., ge=1)
    placed_units: int = Field(..., ge=0)
    service_radius_km: float = Field(..., gt=0)
    total_zones: int = Field(..., ge=0)
    total_weight: int = Field(..., ge=0)
    covered_weight: int = Field(..., ge=0)
    coverage_pct: float = Field(..., ge=0, le=100)
    patrols: list[PatrolUnit]
    uncovered_zones: list[UncoveredZone]