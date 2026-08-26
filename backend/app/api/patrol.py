"""Patrol-plan API route (Prompt 6)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config import (
    PATROL_NUM_UNITS,
    PATROL_SERVICE_RADIUS_KM,
    RISK_EPS_KM,
    RISK_MIN_SAMPLES,
)
from app.database import get_db
from app.patrol_optimizer import optimize_patrols
from app.risk_engine import compute_risk_zones
from app.schemas.patrol import PatrolPlanResponse

router = APIRouter()


@router.get(
    "/patrol-plan",
    response_model=PatrolPlanResponse,
    status_code=200,
    tags=["patrol"],
)
def get_patrol_plan(
    units: int = Query(
        default=PATROL_NUM_UNITS,
        ge=1,
        le=20,
        description="Number of patrol units to place",
    ),
    service_radius_km: float = Query(
        default=PATROL_SERVICE_RADIUS_KM,
        gt=0.0,
        le=25.0,
        description="Coverage radius around each patrol location",
    ),
    eps_km: float = Query(
        default=RISK_EPS_KM,
        gt=0.0,
        le=10.0,
        description="Upstream DBSCAN radius (same meaning as /api/risk-zones)",
    ),
    min_samples: int = Query(
        default=RISK_MIN_SAMPLES,
        ge=1,
        le=50,
        description="Upstream DBSCAN core-point threshold",
    ),
    db: Session = Depends(get_db),
) -> PatrolPlanResponse:
    """Recommend patrol locations over the current DBSCAN risk zones.

    Greedy weighted-coverage placement: higher-risk zones are prioritised and
    every served/uncovered zone is reported explicitly.
    """
    zones = compute_risk_zones(db, eps_km=eps_km, min_samples=min_samples)["zones"]
    return PatrolPlanResponse(**optimize_patrols(zones, units, service_radius_km))