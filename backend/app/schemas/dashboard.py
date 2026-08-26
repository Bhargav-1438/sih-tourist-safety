"""Pydantic schemas for dashboard-facing integration endpoints (Prompt 7).

These are presentation views over the Prompt 5 risk engine and Prompt 6
patrol optimizer: coordinates are emitted as ``[latitude, longitude]`` pairs
so a Leaflet frontend can bind them directly without reshaping.
"""
import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.patrol import UncoveredZone
from app.schemas.risk import RiskLevel


class HeatmapMarker(BaseModel):
    """Leaflet-ready rendering of a single DBSCAN risk zone."""

    zone_id: int = Field(..., ge=1)
    center: list[float] = Field(
        ..., min_length=2, max_length=2,
        description="[latitude, longitude] - feeds L.circle(center, ...)",
    )
    radius_meters: float = Field(..., ge=0)
    risk_score: int = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    point_count: int = Field(..., ge=1)
    incident_count: int = Field(..., ge=1)
    sos_count: int = Field(..., ge=0)
    dominant_incident_type: str = Field(..., min_length=1)
    avg_severity: float = Field(..., gt=0, le=5)
    last_event_at: datetime.datetime


class RiskHeatmapResponse(BaseModel):
    """Envelope returned by GET /api/risk-heatmap."""

    generated_at: datetime.datetime
    eps_km: float = Field(..., gt=0)
    min_samples: int = Field(..., ge=1)
    total_incidents: int = Field(..., ge=0)
    total_sos: int = Field(..., ge=0)
    noise_incidents: int = Field(..., ge=0)
    noise_sos: int = Field(..., ge=0)
    marker_count: int = Field(..., ge=0)
    markers: list[HeatmapMarker]


class ServedZone(BaseModel):
    """Per-zone detail attached to a patrol recommendation."""

    zone_id: int = Field(..., ge=1)
    risk_score: int = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    distance_km: float = Field(..., ge=0, description="Haversine distance from the patrol")


class PatrolRecommendation(BaseModel):
    """A patrol placement enriched for map tooltips."""

    unit_id: int = Field(..., ge=1)
    position: list[float] = Field(
        ..., min_length=2, max_length=2,
        description="[latitude, longitude] - Leaflet marker pair",
    )
    service_radius_km: float = Field(..., gt=0)
    covers_zone_ids: list[int] = Field(..., min_length=1)
    covered_zone_count: int = Field(..., ge=1)
    covered_weight: int = Field(..., ge=0)
    coverage_share_pct: float = Field(..., ge=0, le=100)
    avg_zone_distance_km: float = Field(..., ge=0)
    highest_risk_level: RiskLevel
    served_zones: list[ServedZone] = Field(..., min_length=1)


class PatrolRecommendationsResponse(BaseModel):
    """Envelope returned by GET /api/patrol-recommendations."""

    generated_at: datetime.datetime
    algorithm: Literal["greedy_pmedian_weighted_coverage"]
    requested_units: int = Field(..., ge=1)
    placed_units: int = Field(..., ge=0)
    service_radius_km: float = Field(..., gt=0)
    total_zones: int = Field(..., ge=0)
    total_weight: int = Field(..., ge=0)
    covered_weight: int = Field(..., ge=0)
    coverage_pct: float = Field(..., ge=0, le=100)
    recommendations: list[PatrolRecommendation]
    uncovered_zones: list[UncoveredZone]