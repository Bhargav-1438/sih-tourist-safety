"""Tests for the Prompt 5 DBSCAN risk engine, schemas, and API."""
import datetime
import random

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.database import SessionLocal
from app.main import app
from app.models.incident import Incident, SOSEvent
from app.risk_engine import compute_risk_zones_from_points, level_for_score
from app.schemas.risk import RiskZone

client = TestClient(app)
BASE_TIME = datetime.datetime(2026, 8, 1, 12, 0, 0)
EPS_KM = 0.5
MIN_SAMPLES = 4


@pytest.fixture(autouse=True)
def _isolate_incident_tables():
    """Risk tests wipe incidents/sos_events so seeding is deterministic."""
    db = SessionLocal()
    db.execute(Incident.__table__.delete())
    db.execute(SOSEvent.__table__.delete())
    db.commit()
    db.close()
    yield


def _pt(lat, lon, severity=3, type="theft", kind="incident"):
    return {"kind": kind, "latitude": lat, "longitude": lon,
            "type": type, "severity": severity, "at": BASE_TIME}


def _cluster(lat, lon, n=8, sev=3, typ="theft"):
    """n points packed within roughly +/-50 m of (lat, lon)."""
    return [
        _pt(lat + 0.0004 * ((i % 3) - 1), lon + 0.0004 * (((i // 3) % 3) - 1),
            severity=sev, type=typ)
        for i in range(n)
    ]


def test_two_distant_clusters_produce_two_zones():
    points = _cluster(16.50, 80.61) + _cluster(16.65, 80.45)
    env = compute_risk_zones_from_points(points, EPS_KM, MIN_SAMPLES)
    assert env["zone_count"] == 2
    assert env["total_incidents"] == 16
    assert env["noise_incidents"] == 0
    assert len(env["zones"]) == 2


def test_sparse_points_yield_no_zones():
    points = [_pt(16.40, 80.40), _pt(16.55, 80.55), _pt(16.70, 80.70)]
    env = compute_risk_zones_from_points(points, EPS_KM, MIN_SAMPLES)
    assert env["zone_count"] == 0
    assert env["zones"] == []
    assert env["noise_incidents"] == 3


def test_empty_points_return_zeroed_envelope():
    env = compute_risk_zones_from_points([], EPS_KM, MIN_SAMPLES)
    assert env["zones"] == []
    assert env["zone_count"] == 0
    assert env["total_incidents"] == 0
    assert env["total_sos"] == 0


def test_higher_severity_increases_risk_score():
    low = compute_risk_zones_from_points(_cluster(16.50, 80.61, sev=2), EPS_KM, MIN_SAMPLES)
    high = compute_risk_zones_from_points(_cluster(16.50, 80.61, sev=5), EPS_KM, MIN_SAMPLES)
    assert high["zones"][0]["risk_score"] > low["zones"][0]["risk_score"]


def test_more_points_never_decrease_risk_score():
    small = compute_risk_zones_from_points(_cluster(16.50, 80.61, n=8), EPS_KM, MIN_SAMPLES)
    big = compute_risk_zones_from_points(_cluster(16.50, 80.61, n=24), EPS_KM, MIN_SAMPLES)
    s_small = small["zones"][0]["risk_score"]
    s_big = big["zones"][0]["risk_score"]
    assert s_big >= s_small


def test_level_band_mapping():
    assert level_for_score(10) == "LOW"
    assert level_for_score(30) == "MODERATE"
    assert level_for_score(60) == "HIGH"
    assert level_for_score(90) == "CRITICAL"


def test_zone_radius_is_positive_and_local():
    env = compute_risk_zones_from_points(_cluster(16.50, 80.61), EPS_KM, MIN_SAMPLES)
    radius = env["zones"][0]["radius_meters"]
    assert radius > 0
    assert radius < 1500  # members sit within ~±50 m of the center


def test_output_is_deterministic_under_input_shuffle():
    points = _cluster(16.50, 80.61) + _cluster(16.65, 80.45)
    shuffled = list(points)
    random.Random(7).shuffle(shuffled)
    env_a = compute_risk_zones_from_points(points, EPS_KM, MIN_SAMPLES)
    env_b = compute_risk_zones_from_points(shuffled, EPS_KM, MIN_SAMPLES)
    assert env_a["zones"] == env_b["zones"]
# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------


def _zone(**overrides):
    base = {
        "zone_id": 1,
        "center_latitude": 16.5,
        "center_longitude": 80.6,
        "radius_meters": 120.0,
        "point_count": 8,
        "incident_count": 8,
        "sos_count": 0,
        "dominant_incident_type": "theft",
        "avg_severity": 3.0,
        "distinct_types": 2,
        "last_event_at": BASE_TIME,
        "risk_score": 55,
        "risk_level": "HIGH",
    }
    base.update(overrides)
    return RiskZone(**base)


def test_valid_risk_zone_schema_accepted():
    zone = _zone()
    assert zone.risk_score == 55
    assert zone.risk_level == "HIGH"


def test_risk_zone_rejects_score_above_100():
    with pytest.raises(ValidationError):
        _zone(risk_score=101)


def test_risk_zone_rejects_invalid_latitude():
    with pytest.raises(ValidationError):
        _zone(center_latitude=95.0)


def test_risk_zone_rejects_unknown_level():
    with pytest.raises(ValidationError):
        _zone(risk_level="EXTREME")


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
                occurred_at=BASE_TIME,
            ))
        db.commit()
    finally:
        db.close()


def test_api_returns_zones_sorted_by_score_desc():
    _seed_db_cluster(16.50, 80.61, 12, 4, "theft")
    _seed_db_cluster(16.65, 80.45, 5, 2, "unsafe_area")
    resp = client.get("/api/risk-zones")
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body["zone_count"] == 2
    scores = [z["risk_score"] for z in body["zones"]]
    assert scores == sorted(scores, reverse=True)
    assert body["zones"][0]["point_count"] == 12
    assert body["zones"][0]["dominant_incident_type"] == "theft"
    assert body["total_incidents"] == 17


def test_api_empty_database_returns_empty_zones():
    resp = client.get("/api/risk-zones")
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body["zones"] == []
    assert body["zone_count"] == 0
    assert body["total_incidents"] == 0


def test_api_query_validation_rejects_bad_params():
    resp_zero_eps = client.get("/api/risk-zones", params={"eps_km": 0})
    assert resp_zero_eps.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    resp_zero_ms = client.get("/api/risk-zones", params={"min_samples": 0})
    assert resp_zero_ms.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_sos_events_are_counted_inside_zones():
    _seed_db_cluster(16.50, 80.61, 8, 3, "theft")
    db = SessionLocal()
    try:
        db.add(SOSEvent(tourist_id=1, latitude=16.5001, longitude=80.6101,
                        created_at=BASE_TIME))
        db.commit()
    finally:
        db.close()
    resp = client.get("/api/risk-zones")
    body = resp.json()
    assert body["total_sos"] == 1
    assert sum(z["sos_count"] for z in body["zones"]) == 1