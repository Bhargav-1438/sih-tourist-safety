"""Patrol-recommendation API route (Prompt 7): map-ready enrichment.

Reuses the Prompt 6 optimizer verbatim and enriches each placement with
per-served-zone details (score, level, haversine distance) so a frontend can
render tooltips without extra calls.
"""
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
from app.risk_engine import compute_risk_zones, haversine_km
from app.schemas.dashboard import (
    PatrolRecommendation,
    PatrolRecommendationsResponse,
    ServedZone,
)
from app.schemas.patrol import UncoveredZone

router = APIRouter()


@router.get(
    "/patrol-recommendations",
    response_model=PatrolRecommendationsResponse,
    status_code=200,
    tags=["patrol"],
)
def get_patrol_recommendations(
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
) -> PatrolRecommendationsResponse:
    """Map-ready patrol placements with per-served-zone enrichment."""
    zones = compute_risk_zones(db, eps_km=eps_km, min_samples=min_samples)["zones"]
    plan = optimize_patrols(zones, units, service_radius_km)

    zones_by_id = {z["zone_id"]: z for z in zones}
    recommendations = []
    for p in plan["patrols"]:
        served = []
        for zone_id in p["covers_zone_ids"]:
            z = zones_by_id[zone_id]
            distance = haversine_km(
                p["latitude"], p["longitude"],
                z["center_latitude"], z["center_longitude"],
            )
            served.append(
                ServedZone(
                    zone_id=zone_id,
                    risk_score=z["risk_score"],
                    risk_level=z["risk_level"],
                    distance_km=round(distance, 3),
                )
            )
        served.sort(key=lambda s: s.distance_km)  # nearest first

        recommendations.append(
            PatrolRecommendation(
                unit_id=p["unit_id"],
                position=[p["latitude"], p["longitude"]],
                service_radius_km=service_radius_km,
                covers_zone_ids=p["covers_zone_ids"],
                covered_zone_count=p["covered_zone_count"],
                covered_weight=p["covered_weight"],
                coverage_share_pct=p["coverage_share_pct"],
                avg_zone_distance_km=p["avg_zone_distance_km"],
                highest_risk_level=p["highest_risk_level"],
                served_zones=served,
            )
        )

    return PatrolRecommendationsResponse(
        generated_at=plan["generated_at"],
        algorithm=plan["algorithm"],
        requested_units=plan["requested_units"],
        placed_units=plan["placed_units"],
        service_radius_km=service_radius_km,
        total_zones=plan["total_zones"],
        total_weight=plan["total_weight"],
        covered_weight=plan["covered_weight"],
        coverage_pct=plan["coverage_pct"],
        recommendations=recommendations,
        uncovered_zones=[UncoveredZone(**u) for u in plan["uncovered_zones"]],
    )