"""Tourist registration routes."""
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tourist import Tourist
from app.schemas.tourist import TouristCreate, TouristResponse

router = APIRouter()


@router.post(
    "/register",
    response_model=TouristResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_tourist(
    payload: TouristCreate = Body(...),
    db: Session = Depends(get_db),
) -> TouristResponse:
    """Register a new tourist.

    Returns 201 with the created tourist. Raises 409 if the phone number is
    already registered, and 422 if the input is invalid.
    """
    existing = (
        db.execute(select(Tourist).where(Tourist.phone == payload.phone))
        .scalar_one_or_none()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A tourist with this phone number is already registered.",
        )

    tourist = Tourist(name=payload.name, phone=payload.phone)
    db.add(tourist)
    try:
        db.commit()
    except IntegrityError:
        # Defensive guard against race conditions; the unique DB constraint is
        # the final authority on duplicates.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A tourist with this phone number is already registered.",
        )
    db.refresh(tourist)
    return TouristResponse.model_validate(tourist)
