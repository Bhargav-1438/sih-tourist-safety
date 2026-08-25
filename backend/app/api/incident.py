"""Incident retrieval routes."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.incident import Incident
from app.schemas.incident import IncidentResponse

router = APIRouter()


@router.get(
    "/incidents",
    response_model=list[IncidentResponse],
    status_code=200,
)
def list_incidents(db: Session = Depends(get_db)) -> list[IncidentResponse]:
    """Return all recorded incidents (synthetic demo dataset)."""
    incidents = db.execute(select(Incident)).scalars().all()
    return [IncidentResponse.model_validate(i) for i in incidents]