"""SQLAlchemy models for safety incidents and SOS events.

Models:
    Incident  -- a historical safety incident (synthetic demo data).
    SOSEvent  -- an emergency SOS event reported by a tourist.
"""
import datetime

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Incident(Base):
    """A historical safety incident (synthetic demo data)."""

    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)
    incident_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[int] = mapped_column(nullable=False)
    occurred_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"<Incident id={self.id!r} type={self.incident_type!r} "
            f"severity={self.severity!r}>"
        )


class SOSEvent(Base):
    """An emergency SOS event reported by a tourist."""

    __tablename__ = "sos_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tourist_id: Mapped[int] = mapped_column(nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default="active",
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"<SOSEvent id={self.id!r} tourist_id={self.tourist_id!r} "
            f"status={self.status!r}>"
        )