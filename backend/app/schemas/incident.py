"""Pydantic schemas for incidents and SOS events."""
import datetime

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Incident types (simple strings, as specified by the prototype)
# ---------------------------------------------------------------------------
INCIDENT_TYPES = (
    "theft",
    "harassment",
    "medical",
    "accident",
    "missing_person",
    "unsafe_area",
)


class IncidentBase(BaseModel):
    """Fields shared by incident create/response schemas."""

    latitude: float = Field(..., ge=-90, le=90, description="Valid latitude -90..90")
    longitude: float = Field(..., ge=-180, le=180, description="Valid longitude -180..180")
    incident_type: str = Field(..., min_length=1, max_length=50)
    severity: int = Field(..., ge=1, le=5, description="Severity level 1 (low) to 5 (high)")
    occurred_at: datetime.datetime


class IncidentCreate(IncidentBase):
    """Payload for creating a new incident."""


class IncidentResponse(IncidentBase):
    """Response body for an incident record."""

    model_config = ConfigDict(from_attributes=True)

    id: int


class SOSCreate(BaseModel):
    """Payload for creating an SOS event.

    The `status` field is intentionally omitted — it is set by the server
    (default "active") and cannot be supplied by the client.
    """

    tourist_id: int = Field(..., gt=0, description="Must be a positive integer")
    latitude: float = Field(..., ge=-90, le=90, description="Valid latitude -90..90")
    longitude: float = Field(..., ge=-180, le=180, description="Valid longitude -180..180")


class SOSResponse(BaseModel):
    """Response body for an SOS event."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    tourist_id: int
    latitude: float
    longitude: float
    status: str
    created_at: datetime.datetime


class SOSListResponse(BaseModel):
    """Response body for a list of SOS events."""

    sos_events: list[SOSResponse]