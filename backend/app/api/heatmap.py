"""Risk-heatmap API route (Prompt 7): Leaflet-friendly view of risk zones.

Pure presentation adapter over the Prompt 5 engine - no clustering logic.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config import RISK_EPS_KM, RISK_MIN_SAMPLES
from app.database import get_db
from app.risk_engine import compute_risk_zones
from app.schemas.dashboard import HeatmapMarker, RiskHeatmapResponse

router = APIRouter()


@router.get(
    "/risk-heatmap",
    response_model=RiskHeatmapResponse,
    status_code=200,
    tags=["risk"],
)
def get_risk_heatmap(
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
) -> RiskHeatmapResponse:
    """Reshape risk zones into Leaflet-ready markers (center pairs + radii)."""
    result = compute_risk_zones(db, eps_km=eps_km, min_samples=min_samples)

    markers = [
        HeatmapMarker(
            zone_id=z["zone_id"],
            center=[z["center_latitude"], z["center_longitude"]],
            radius_meters=z["radius_meters"],
            risk_score=z["risk_score"],
            risk_level=z["risk_level"],
            point_count=z["point_count"],
            incident_count=z["incident_count"],
            sos_count=z["sos_count"],
            dominant_incident_type=z["dominant_incident_type"],
            avg_severity=z["avg_severity"],
            last_event_at=z["last_event_at"],
        )
        for z in result["zones"]  # engine order: risk_score desc (deterministic)
    ]

    return RiskHeatmapResponse(
        generated_at=result["generated_at"],
        eps_km=result["eps_km"],
        min_samples=result["min_samples"],
        total_incidents=result["total_incidents"],
        total_sos=result["total_sos"],
        noise_incidents=result["noise_incidents"],
        noise_sos=result["noise_sos"],
        marker_count=len(markers),
        markers=markers,
    )