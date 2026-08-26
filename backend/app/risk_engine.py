"""DBSCAN-based geographic risk engine.

Reads incident + SOS points from the database, clusters them spatially with
DBSCAN (haversine metric on radian coordinates) and scores each cluster as a
risk zone. Pure computation: no caching tables, no persistence.

NOTE: in this prototype the incident rows are SYNTHETIC demo data generated
by scripts/generate_incidents.py (seed 42, Vijayawada bounding box).
"""
import datetime
import math
from collections import Counter

from sklearn.cluster import DBSCAN
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.incident import Incident, SOSEvent

EARTH_RADIUS_KM = 6371.0088

# Multiplier applied to an event severity before averaging (viva table).
TYPE_WEIGHTS = {
    "theft": 1.0,
    "harassment": 1.2,
    "medical": 1.3,
    "accident": 1.2,
    "missing_person": 1.5,
    "unsafe_area": 0.8,
    "sos": 1.4,  # an active distress call is treated as urgent
}

# Score component weights (intentionally sum to 1.0).
W_DENSITY = 0.45
W_SEVERITY = 0.40
W_VARIETY = 0.15
DENSITY_SATURATION_POINTS = 25
VARIETY_NORMALIZER = len(TYPE_WEIGHTS)  # 6 incident types + "sos"

# risk_score -> risk_level bands (checked highest threshold first).
LEVEL_BANDS = (
    (75, "CRITICAL"),
    (50, "HIGH"),
    (25, "MODERATE"),
    (0, "LOW"),
)

SOS_EFFECTIVE_SEVERITY = 5


def level_for_score(score: int) -> str:
    """Map a clamped 0-100 score onto its risk-level band."""
    for threshold, name in LEVEL_BANDS:
        if score >= threshold:
            return name
    return "LOW"  # defensive fallback; scores are clamped to >= 0


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two degree coordinates, in km."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def load_risk_points(db: Session) -> list[dict]:
    """Load incidents + SOS events as one uniform point list."""
    points: list[dict] = []
    for inc in db.execute(select(Incident)).scalars():
        points.append(
            {
                "kind": "incident",
                "latitude": inc.latitude,
                "longitude": inc.longitude,
                "type": inc.incident_type,
                "severity": inc.severity,
                "at": inc.occurred_at,
            }
        )
    for sos in db.execute(select(SOSEvent)).scalars():
        points.append(
            {
                "kind": "sos",
                "latitude": sos.latitude,
                "longitude": sos.longitude,
                "type": "sos",
                "severity": SOS_EFFECTIVE_SEVERITY,
                "at": sos.created_at,
            }
        )
    return points


def _score_zone(members: list[dict]) -> tuple[int, float, int]:
    """Return (risk_score 0-100, mean raw severity, distinct type count)."""
    n = len(members)
    avg_severity = sum(m["severity"] for m in members) / n
    weighted = [m["severity"] * TYPE_WEIGHTS.get(m["type"], 1.0) for m in members]
    severity_component = min(sum(weighted) / n / 5.0, 1.0)
    density_component = min(1.0, n / DENSITY_SATURATION_POINTS)
    distinct = len({m["type"] for m in members})
    variety_component = min(1.0, distinct / VARIETY_NORMALIZER)
    raw = W_DENSITY * density_component + W_SEVERITY * severity_component + W_VARIETY * variety_component
    score = int(max(0, min(100, round(100 * raw))))
    return score, avg_severity, distinct


def compute_risk_zones_from_points(
    points: list[dict], eps_km: float, min_samples: int
) -> dict:
    """Cluster pre-loaded points and return the RiskZonesResponse payload dict."""
    total_incidents = sum(1 for p in points if p["kind"] == "incident")
    total_sos = len(points) - total_incidents
    envelope = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc),
        "eps_km": eps_km,
        "min_samples": min_samples,
        "total_incidents": total_incidents,
        "total_sos": total_sos,
        "noise_incidents": 0,
        "noise_sos": 0,
        "zone_count": 0,
        "zones": [],
    }
    if not points:
        return envelope

    coords = [
        [math.radians(p["latitude"]), math.radians(p["longitude"])] for p in points
    ]
    labels = DBSCAN(
        eps=eps_km / EARTH_RADIUS_KM, min_samples=min_samples, metric="haversine"
    ).fit_predict(coords)

    clusters: dict[int, list[dict]] = {}
    for point, label in zip(points, labels):
        if label == -1:
            if point["kind"] == "incident":
                envelope["noise_incidents"] += 1
            else:
                envelope["noise_sos"] += 1
        else:
            clusters.setdefault(label, []).append(point)

    zones = []
    for members in clusters.values():
        n = len(members)
        center_lat = sum(m["latitude"] for m in members) / n
        center_lon = sum(m["longitude"] for m in members) / n
        radius_m = (
            max(
                _haversine_km(center_lat, center_lon, m["latitude"], m["longitude"])
                for m in members
            )
            * 1000.0
        )
        score, avg_severity, distinct = _score_zone(members)
        type_counts = Counter(m["type"] for m in members)
        dominant = sorted(type_counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        zones.append(
            {
                "zone_id": 0,  # assigned after deterministic sorting below
                "center_latitude": round(center_lat, 6),
                "center_longitude": round(center_lon, 6),
                "radius_meters": round(max(radius_m, 1.0), 1),
                "point_count": n,
                "incident_count": sum(1 for m in members if m["kind"] == "incident"),
                "sos_count": sum(1 for m in members if m["kind"] == "sos"),
                "dominant_incident_type": dominant,
                "avg_severity": round(avg_severity, 2),
                "distinct_types": distinct,
                "last_event_at": max(m["at"] for m in members),
                "risk_score": score,
                "risk_level": level_for_score(score),
            }
        )

    # Deterministic ordering independent of DBSCAN label numbering.
    zones.sort(
        key=lambda z: (-z["risk_score"], z["center_latitude"], z["center_longitude"])
    )
    for idx, zone in enumerate(zones, start=1):
        zone["zone_id"] = idx

    envelope["zone_count"] = len(zones)
    envelope["zones"] = zones
    return envelope


def compute_risk_zones(db: Session, eps_km: float, min_samples: int) -> dict:
    """Load points from the database and compute risk zones."""
    return compute_risk_zones_from_points(
        load_risk_points(db), eps_km=eps_km, min_samples=min_samples
    )