"""Prompt 7 integration tests: heatmap + patrol recommendations."""
import datetime

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.incident import Incident, SOSEvent
from app.risk_engine import haversine_km

client = TestClient(app)

# Legacy response key sets that MUST remain stable (backward compatibility).
RISK_ENVELOPE_KEYS = {
    "generated_at", "eps_km", "min_samples", "total_incidents",
    "total_sos", "noise_incidents", "noise_sos", "zone_count", "zones",
}
ZONE_KEYS = {
    "zone_id", "center_latitude", "center_longitude", "radius_meters",
    "point_count", "incident_count", "sos_count", "dominant_incident_type",
    "avg_severity", "distinct_types", "last_event_at", "risk_score",
    "risk_level",
}
PATROL_PLAN_KEYS = {
    "generated_at", "algorithm", "requested_units", "placed_units",
    "service_radius_km", "total_zones", "total_weight", "covered_weight",
    "coverage_pct", "patrols", "uncovered_zones",
}
PATROL_UNIT_KEYS = {
    "unit_id", "latitude", "longitude", "covers_zone_ids",
    "covered_zone_count", "covered_weight", "coverage_share_pct",
    "avg_zone_distance_km", "highest_risk_level",
}


@pytest.fixture(autouse=True)
def _isolate_event_tables():
    """Integration tests start from empty incidents/sos_events tables."""
    db = SessionLocal()
    db.execute(Incident.__table__.delete())
    db.execute(SOSEvent.__table__.delete())
    db.commit()
    db.close()
    yield


def _seed_db_cluster(lat, lon, n, sev, typ):
    db = SessionLocal()
    try:
        for i in range(n):
            db.add(Incident(
                latitude=lat + 0.0004 * ((i % 3) - 1),
                longitude=lon + 0.0004 * (((i // 3) % 3) - 1),
                incident_type=typ,
                severity=sev,
                occurred_at=datetime.datetime(2026, 8, 1, 12, 0, 0),
            ))
        db.commit()
    finally:
        db.close()


def _seed_two_far_clusters():
    # ~22 km apart: far beyond clustering eps (and the default 2 km patrol
    # radius), yet within the API-capped 25 km service radius when needed.
    _seed_db_cluster(16.50, 80.61, 12, 4, "theft")
    _seed_db_cluster(16.62, 80.78, 6, 2, "unsafe_area")


# ---------------------------------------------------------------------------
# GET /api/risk-heatmap
# ---------------------------------------------------------------------------


def test_heatmap_matches_risk_zones_cross_endpoint():
    _seed_two_far_clusters()
    zones_body = client.get("/api/risk-zones").json()
    heat_body = client.get("/api/risk-heatmap").json()
    assert heat_body["marker_count"] == zones_body["zone_count"] == 2
    assert heat_body["total_incidents"] == zones_body["total_incidents"] == 18
    assert heat_body["noise_incidents"] == zones_body["noise_incidents"]


def test_heatmap_markers_sorted_desc_and_centers_match():
    _seed_two_far_clusters()
    zones_body = client.get("/api/risk-zones").json()
    markers = client.get("/api/risk-heatmap").json()["markers"]
    scores = [m["risk_score"] for m in markers]
    assert scores == sorted(scores, reverse=True)
    zone_centers = {(z["center_latitude"], z["center_longitude"])
                    for z in zones_body["zones"]}
    marker_centers = {tuple(m["center"]) for m in markers}
    assert marker_centers == zone_centers


def test_heatmap_empty_database_returns_no_markers():
    body = client.get("/api/risk-heatmap").json()
    assert body["markers"] == []
    assert body["marker_count"] == 0
    assert body["total_incidents"] == 0


def test_heatmap_rejects_invalid_eps_km():
    resp = client.get("/api/risk-heatmap", params={"eps_km": 0})
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_heatmap_is_deterministic_across_calls():
    _seed_two_far_clusters()
    a = client.get("/api/risk-heatmap").json()["markers"]
    b = client.get("/api/risk-heatmap").json()["markers"]
    assert a == b
# ---------------------------------------------------------------------------
# GET /api/patrol-recommendations
# ---------------------------------------------------------------------------


def test_recommendations_positions_match_chosen_zone_centers():
    _seed_two_far_clusters()
    body = client.get("/api/patrol-recommendations", params={"units": 2}).json()
    assert body["placed_units"] == 2
    expected = {(16.50, 80.61), (16.62, 80.78)}
    for rec in body["recommendations"]:
        lat, lon = rec["position"]
        assert min(abs(lat - e[0]) + abs(lon - e[1]) for e in expected) < 0.01
    assert body["uncovered_zones"] == []


def test_recommendations_served_zones_enrichment():
    _seed_two_far_clusters()
    # Huge radius + single unit => every zone served by one recommendation.
    body = client.get(
        "/api/patrol-recommendations",
        params={"units": 1, "service_radius_km": 25},
    ).json()
    assert body["placed_units"] == 1
    rec = body["recommendations"][0]
    served = rec["served_zones"]
    assert len(served) == body["total_zones"] == 2
    distances = [s["distance_km"] for s in served]
    assert distances == sorted(distances)  # nearest first
    assert all(d <= 25.0 for d in distances)
    # Reported distance must match an independent haversine recomputation.
    plat, plon = rec["position"]
    for s in served:
        zone = next(z for z in client.get("/api/risk-zones").json()["zones"]
                    if z["zone_id"] == s["zone_id"])
        expected = haversine_km(plat, plon,
                                zone["center_latitude"], zone["center_longitude"])
        assert abs(s["distance_km"] - round(expected, 3)) <= 0.0011


def test_recommendations_empty_database_returns_empty_plan():
    body = client.get("/api/patrol-recommendations").json()
    assert body["recommendations"] == []
    assert body["placed_units"] == 0
    assert body["coverage_pct"] == 0.0


def test_recommendations_reject_invalid_query_params():
    r1 = client.get("/api/patrol-recommendations", params={"units": 0})
    assert r1.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    r2 = client.get("/api/patrol-recommendations", params={"service_radius_km": -1})
    assert r2.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_recommendations_single_unit_targets_critical_cluster():
    _seed_db_cluster(16.50, 80.61, 14, 5, "missing_person")  # critical weight
    _seed_db_cluster(17.30, 81.50, 4, 1, "unsafe_area")       # low weight, far
    body = client.get("/api/patrol-recommendations", params={"units": 1}).json()
    assert body["placed_units"] == 1
    lat, lon = body["recommendations"][0]["position"]
    d_crit = abs(lat - 16.50) + abs(lon - 80.61)
    d_low = abs(lat - 17.30) + abs(lon - 81.50)
    assert d_crit < d_low


# ---------------------------------------------------------------------------
# Backward compatibility + integration chain + router hygiene
# ---------------------------------------------------------------------------


def test_legacy_endpoints_keep_their_exact_key_sets():
    _seed_two_far_clusters()
    zones_body = client.get("/api/risk-zones").json()
    assert set(zones_body.keys()) == RISK_ENVELOPE_KEYS
    assert set(zones_body["zones"][0].keys()) == ZONE_KEYS

    plan_body = client.get("/api/patrol-plan", params={"units": 2}).json()
    assert set(plan_body.keys()) == PATROL_PLAN_KEYS
    assert set(plan_body["patrols"][0].keys()) == PATROL_UNIT_KEYS


def test_chain_incidents_to_heatmap_totals_agree():
    _seed_two_far_clusters()
    incidents = client.get("/api/incidents").json()
    heat = client.get("/api/risk-heatmap").json()
    assert heat["total_incidents"] == len(incidents) == 18
    assert sum(m["incident_count"] for m in heat["markers"]) + heat["noise_incidents"] == 18


def test_router_paths_are_registered_exactly_once():
    def walk(router):
        """Collect every string path, descending into nested/wrapped routers.

        Newer FastAPI versions wrap ``include_router`` targets in an
        ``_IncludedRouter`` object whose real router lives under
        ``original_router``, so we probe several known attribute names.
        """
        found = []
        for r in router.routes:
            path = getattr(r, "path", None)
            if isinstance(path, str):
                found.append(path)
            for attr in ("routes", "router", "original_router"):
                nested = getattr(r, attr, None)
                if nested is not None and hasattr(nested, "routes"):
                    found.extend(walk(nested))
                    break
        return found

    paths = walk(app)
    heatmap_hits = [p for p in paths if p.endswith("/risk-heatmap")]
    patrol_hits = [p for p in paths if p.endswith("/patrol-recommendations")]
    assert len(heatmap_hits) == 1  # registered exactly once
    assert len(patrol_hits) == 1
    # No duplicated API registration anywhere in the tree.
    api_paths = [p for p in paths if p.startswith("/api")]
    assert {p for p in api_paths if api_paths.count(p) > 1} == set()