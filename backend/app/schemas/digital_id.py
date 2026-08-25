"""Pydantic schemas for the digital-ID / QR verification feature."""
import datetime

from pydantic import BaseModel


class DigitalIdRequest(BaseModel):
    """Payload for POST /api/verify-id."""

    token: str


class DigitalIdResponse(BaseModel):
    """Response body returned by POST /api/digital-id/{tourist_id}."""

    tourist_id: int
    token: str
    expires_at: datetime.datetime
    qr_code: str


class VerifiedTourist(BaseModel):
    """Minimal tourist info returned after a successful verification."""

    id: int
    name: str


class VerifyResponse(BaseModel):
    """Response body returned by POST /api/verify-id."""

    valid: bool
    tourist: VerifiedTourist | None = None
