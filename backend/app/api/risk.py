"""Risk-zone API route (Prompt 5)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config import RISK_EPS_KM, RISK_MIN_SAMPLES
from app.database import get_db
from app.risk_engine import compute_risk_zones
from app.schemas.risk import RiskZonesResponse

router = APIRouter()


@router.get(
    "/risk-zones",
    response_model=RiskZonesResponse,
    status_code=200,
    tags=["risk"],
)
def get_risk_zones(
    eps_km: float = Query(
        default=RISK_EPS_KM,
        gt=0.0,
        le=10.0,
        description="DBSCAN neighbourhood radius in kilometres (~0.5 default)",
    ),
    min_samples: int = Query(
        default=RISK_MIN_SAMPLES,
        ge=1,
        le=50,
        description="Minimum nearby points required to form a dense zone",
    ),
    db: Session = Depends(get_db),
) -> RiskZonesResponse:
    """Cluster incidents + SOS events into scored geographic risk zones.

    Read-only computation over the current database contents; safe to poll.
    """
    result = compute_risk_zones(db, eps_km=eps_km, min_samples=min_samples)
    return RiskZonesResponse(**result)