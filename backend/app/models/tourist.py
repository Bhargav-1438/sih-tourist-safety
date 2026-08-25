"""SQLAlchemy model for a tourist."""
import datetime

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Tourist(Base):
    """Minimal tourist profile registered before a trip."""

    __tablename__ = "tourists"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Stored as a string (never an integer) so leading zeros / formatting are
    # preserved. Unique per tourist to prevent duplicate registrations.
    phone: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Tourist id={self.id!r} name={self.name!r} phone={self.phone!r}>"
