"""Tests for the Prompt 6 patrol optimizer, schemas, and API."""
import datetime
import random

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.database import SessionLocal
from app.main import app
from app.models.incident import Incident
from app.patrol_optimizer import optimize_patrols
from app.schemas.patrol import PatrolUnit

client = TestClient(app)

RADIUS = 2.0  # km; generous so same-city zones cover themselves trivially


@pytest.fixture(autouse=True)
def _isolate_incident_tables():
    """Patrol tests start from empty incidents/sos_events tables."""
    db = SessionLocal()
    db.execute(Incident.__table__.delete())
    from app.models.incident import SOSEvent
    db.execute(SOSEvent.__table__.delete())
    db.commit()
    db.close()
    yield


def _zone(zid, score, lat, lon, level="HIGH"):
    """Minimal zone dict in the exact shape the Prompt 5 engine emits."""
    return {
        "zone_id": zid,
        "risk_score": score,
        "risk_level": level,
        "center_latitude": lat,
        "center_longitude": lon,
    }


# ---------------------------------------------------------------------------
# Pure optimizer
# ---------------------------------------------------------------------------


def test_two_far_zones_two_units_each_covers_own_zone():
    zones = [_zone(1, 80, 16.50, 80.60), _zone(2, 70, 17.20, 81.40)]
    plan = optimize_patrols(zones, num_units=2, service_radius_km=RADIUS)
    assert plan["placed_units"] == 2
    assert plan["uncovered_zones"] == []
    assert plan["patrols"][0]["covers_zone_ids"] == [1]
    assert plan["patrols"][1]["covers_zone_ids"] == [2]
    assert plan["covered_weight"] == plan["total_weight"] == 150
    assert plan["coverage_pct"] == 100.0


def test_units_exceed_zones_places_one_per_zone():
    zones = [_zone(1, 80, 16.50, 80.60), _zone(2, 70, 17.20, 81.40)]
    plan = optimize_patrols(zones, num_units=5, service_radius_km=RADIUS)
    assert plan["requested_units"] == 5
    assert plan["placed_units"] == 2
    assert plan["patrols"][0]["unit_id"] == 1
    assert plan["patrols"][1]["unit_id"] == 2


def test_empty_zones_return_zeroed_plan():
    plan = optimize_patrols([], num_units=3, service_radius_km=RADIUS)
    assert plan["patrols"] == []
    assert plan["placed_units"] == 0
    assert plan["total_zones"] == 0
    assert plan["total_weight"] == 0
    assert plan["coverage_pct"] == 0.0
    assert plan["uncovered_zones"] == []


def test_single_unit_prefers_highest_weight_zone():
    zones = [
        _zone(1, 90, 16.50, 80.60, level="CRITICAL"),
        _zone(2, 60, 16.80, 80.90),
        _zone(3, 30, 17.10, 81.20),
    ]
    plan = optimize_patrols(zones, num_units=1, service_radius_km=RADIUS)
    assert plan["placed_units"] == 1
    top = plan["patrols"][0]
    assert top["covers_zone_ids"] == [1]
    assert top["latitude"] == 16.50 and top["longitude"] == 80.60
    assert top["highest_risk_level"] == "CRITICAL"
    uncovered_ids = [u["zone_id"] for u in plan["uncovered_zones"]]
    assert uncovered_ids == [2, 3]  # sorted by risk_score desc


def test_radius_limits_chain_coverage():
    # Three collinear zones ~3 km apart: with R=2 none covers a neighbour.
    zones = [
        _zone(1, 50, 16.500, 80.600),
        _zone(2, 50, 16.527, 80.600),
        _zone(3, 50, 16.554, 80.600),
    ]
    plan = optimize_patrols(zones, num_units=2, service_radius_km=RADIUS)
    assert all(p["covered_zone_count"] == 1 for p in plan["patrols"])
    assert len(plan["uncovered_zones"]) == 1


def test_output_is_deterministic_under_input_shuffle():
    zones = [
        _zone(1, 90, 16.50, 80.60),
        _zone(2, 75, 17.20, 81.40),
        _zone(3, 40, 16.30, 80.30),
    ]
    shuffled = list(zones)
    random.Random(11).shuffle(shuffled)
    a = optimize_patrols(zones, 2, RADIUS)
    b = optimize_patrols(shuffled, 2, RADIUS)
    assert a["patrols"] == b["patrols"]
    assert a["uncovered_zones"] == b["uncovered_zones"]
    assert a["coverage_pct"] == b["coverage_pct"]
# ---------------------------------------------------------------------------
# Coverage math
# ---------------------------------------------------------------------------


def test_full_coverage_share_math():
    zones = [_zone(1, 90, 16.50, 80.60), _zone(2, 60, 16.505, 80.605)]
    plan = optimize_patrols(zones, num_units=1, service_radius_km=RADIUS)
    # Both centers are ~0.7 km apart, so one patrol covers both.
    assert plan["placed_units"] == 1
    unit = plan["patrols"][0]
    assert unit["covered_weight"] == 150 == plan["total_weight"]
    assert unit["coverage_share_pct"] == 100.0
    assert plan["coverage_pct"] == 100.0
    assert unit["avg_zone_distance_km"] <= RADIUS


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------


def _unit(**overrides):
    base = {
        "unit_id": 1,
        "latitude": 16.5,
        "longitude": 80.6,
        "covers_zone_ids": [1],
        "covered_zone_count": 1,
        "covered_weight": 80,
        "coverage_share_pct": 40.0,
        "avg_zone_distance_km": 0.5,
        "highest_risk_level": "CRITICAL",
    }
    base.update(overrides)
    return PatrolUnit(**base)


def test_valid_patrol_unit_schema_accepted():
    unit = _unit()
    assert unit.unit_id == 1
    assert unit.highest_risk_level == "CRITICAL"


def test_patrol_unit_rejects_share_above_100():
    with pytest.raises(ValidationError):
        _unit(coverage_share_pct=100.01)


def test_patrol_unit_rejects_unknown_level():
    with pytest.raises(ValidationError):
        _unit(highest_risk_level="EXTREME")


def test_patrol_unit_rejects_negative_covered_weight():
    with pytest.raises(ValidationError):
        _unit(covered_weight=-5)


# ---------------------------------------------------------------------------
# API endpoint (ORM-seeded database)
# ---------------------------------------------------------------------------


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


def test_api_places_two_units_for_two_separated_clusters():
    import datetime as _dt
    _seed_db_cluster(16.50, 80.61, 12, 4, "theft")
    db = SessionLocal()
    try:
        for i in range(6):
            db.add(Incident(
                latitude=17.20 + 0.0004 * ((i % 3) - 1),
                longitude=81.40 + 0.0004 * (((i // 3) % 3) - 1),
                incident_type="unsafe_area",
                severity=2,
                occurred_at=_dt.datetime(2026, 8, 1, 12, 0, 0),
            ))
        db.commit()
    finally:
        db.close()

    resp = client.get("/api/patrol-plan", params={"units": 2})
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body["algorithm"] == "greedy_pmedian_weighted_coverage"
    assert body["requested_units"] == 2
    assert body["placed_units"] == 2
    assert [p["unit_id"] for p in body["patrols"]] == [1, 2]
    assert body["uncovered_zones"] == []
    assert body["coverage_pct"] == 100.0
    # First unit goes to the higher-weight cluster.
    assert body["patrols"][0]["highest_risk_level"] in {"CRITICAL", "HIGH"}


def test_api_empty_database_returns_empty_plan():
    resp = client.get("/api/patrol-plan")
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body["patrols"] == []
    assert body["placed_units"] == 0
    assert body["total_weight"] == 0
    assert body["coverage_pct"] == 0.0


def test_api_query_validation_rejects_bad_params():
    r1 = client.get("/api/patrol-plan", params={"units": 0})
    assert r1.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    r2 = client.get("/api/patrol-plan", params={"service_radius_km": 0})
    assert r2.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_api_single_unit_goes_to_critical_cluster():
    import datetime as _dt
    _seed_db_cluster(16.50, 80.61, 14, 5, "missing_person")   # critical weight
    _seed_db_cluster(17.30, 81.50, 4, 1, "unsafe_area")       # low weight, far away
    resp = client.get("/api/patrol-plan", params={"units": 1})
    body = resp.json()
    assert body["placed_units"] == 1
    patrol = body["patrols"][0]
    dist_to_critical = abs(patrol["latitude"] - 16.50) + abs(patrol["longitude"] - 80.61)
    dist_to_low = abs(patrol["latitude"] - 17.30) + abs(patrol["longitude"] - 81.50)
    assert dist_to_critical < dist_to_low
    assert len(body["uncovered_zones"]) == 1