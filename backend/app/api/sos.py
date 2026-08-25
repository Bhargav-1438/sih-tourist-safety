"""SOS event routes."""
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.incident import SOSEvent
from app.models.tourist import Tourist
from app.schemas.incident import SOSCreate, SOSListResponse, SOSResponse

router = APIRouter()


@router.post(
    "/sos",
    response_model=SOSResponse,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"description": "Tourist not found"}},
)
def create_sos_event(
    payload: SOSCreate = Body(...),
    db: Session = Depends(get_db),
) -> SOSResponse:
    """Record an emergency SOS event for an existing tourist.

    The tourist must exist; otherwise HTTP 404 is returned.
    """
    tourist = db.get(Tourist, payload.tourist_id)
    if tourist is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tourist with id {payload.tourist_id} not found.",
        )

    sos = SOSEvent(
        tourist_id=payload.tourist_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    db.add(sos)
    db.commit()
    db.refresh(sos)
    return SOSResponse.model_validate(sos)


@router.get(
    "/sos",
    response_model=SOSListResponse,
    status_code=status.HTTP_200_OK,
)
def list_sos_events(db: Session = Depends(get_db)) -> SOSListResponse:
    """Return all stored SOS events (for the authority dashboard)."""
    events = db.execute(select(SOSEvent)).scalars().all()
    return SOSListResponse(
        sos_events=[SOSResponse.model_validate(e) for e in events]
    )