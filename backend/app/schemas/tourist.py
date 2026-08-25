"""Pydantic schemas for tourist registration."""
import datetime
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Indian mobile numbers: exactly 10 digits, the first digit must be 6-9.
_INDIAN_MOBILE_RE = re.compile(r"^[6-9]\d{9}$")


class TouristCreate(BaseModel):
    """Payload for POST /api/register."""

    name: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(..., min_length=1, max_length=20)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("name must not be empty or whitespace")
        return value.strip()

    @field_validator("phone")
    @classmethod
    def normalize_and_validate_phone(cls, value: str) -> str:
        """Accept Indian 10-digit mobile numbers, with an optional country code."""
        if not isinstance(value, str):
            raise ValueError("phone must be a string")
        # Keep digits and a leading '+' but drop separators.
        cleaned = re.sub(r"[\s\-()]", "", value)
        if not cleaned:
            raise ValueError(
                "phone must be a valid 10-digit Indian mobile number starting with 6-9"
            )
        # Drop an optional country code ("+91" or "91") when it is a prefix.
        if cleaned.startswith("+91"):
            cleaned = cleaned[3:]
        elif cleaned.startswith("91") and len(cleaned) > 10:
            cleaned = cleaned[2:]
        if not _INDIAN_MOBILE_RE.match(cleaned):
            raise ValueError(
                "phone must be a valid 10-digit Indian mobile number starting with 6-9"
            )
        return cleaned


class TouristResponse(BaseModel):
    """Response body returned after a successful registration."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str
    created_at: datetime.datetime
