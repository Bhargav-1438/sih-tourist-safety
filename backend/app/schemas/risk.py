"""Pydantic schemas for the DBSCAN-based geographic risk engine."""
import datetime
from typing import Literal

from pydantic import BaseModel, Field

RiskLevel = Literal["LOW", "MODERATE", "HIGH", "CRITICAL"]


class RiskZone(BaseModel):
    """A single geographic risk zone produced by DBSCAN clustering."""

    zone_id: int = Field(..., ge=1, description="1-based rank, ordered by risk_score desc")
    center_latitude: float = Field(..., ge=-90, le=90)
    center_longitude: float = Field(..., ge=-180, le=180)
    radius_meters: float = Field(..., ge=0, description="Max distance from center to a member")
    point_count: int = Field(..., ge=1)
    incident_count: int = Field(..., ge=1)
    sos_count: int = Field(..., ge=0)
    dominant_incident_type: str = Field(..., min_length=1)
    avg_severity: float = Field(..., gt=0, le=5, description="Mean raw severity of members")
    distinct_types: int = Field(..., ge=1)
    last_event_at: datetime.datetime
    risk_score: int = Field(..., ge=0, le=100)
    risk_level: RiskLevel


class RiskZonesResponse(BaseModel):
    """Envelope returned by GET /api/risk-zones."""

    generated_at: datetime.datetime
    eps_km: float = Field(..., gt=0)
    min_samples: int = Field(..., ge=1)
    total_incidents: int = Field(..., ge=0)
    total_sos: int = Field(..., ge=0)
    noise_incidents: int = Field(..., ge=0, description="Incidents not assigned to any zone")
    noise_sos: int = Field(..., ge=0, description="SOS events not assigned to any zone")
    zone_count: int = Field(..., ge=0)
    zones: list[RiskZone]