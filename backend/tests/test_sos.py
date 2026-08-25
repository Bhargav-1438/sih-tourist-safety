""""""Tests for the SOS schema validation."""
import pytest
from pydantic import ValidationError

from app.schemas.incident import SOSCreate


def _valid_sos_data(**overrides):
    """Return a dict of valid SOS fields, with selective overrides."""
    base = {
        "tourist_id": 1,
        "latitude": 16.5044,
        "longitude": 80.4101,
    }
    base.update(overrides)
    return base


def test_valid_sos_schema_accepted():
    """A well-formed SOS payload validates successfully."""
    sos = SOSCreate(**_valid_sos_data())
    assert sos.tourist_id == 1
    assert sos.latitude == 16.5044
    assert sos.longitude == 80.4101


def test_invalid_sos_latitude_rejected():
    """Latitude above 90 is rejected."""
    with pytest.raises(ValidationError):
        SOSCreate(**_valid_sos_data(latitude=95.0))


def test_latitude_below_ninety_rejected():
    """Latitude below -90 is rejected."""
    with pytest.raises(ValidationError):
        SOSCreate(**_valid_sos_data(latitude=-91.0))


def test_invalid_sos_longitude_rejected():
    """Longitude above 180 is rejected."""
    with pytest.raises(ValidationError):
        SOSCreate(**_valid_sos_data(longitude=200.0))


def test_longitude_below_minus180_rejected():
    """Longitude below -180 is rejected."""
    with pytest.raises(ValidationError):
        SOSCreate(**_valid_sos_data(longitude=-181.0))


def test_invalid_tourist_id_rejected():
    """tourist_id must be a positive integer (zero rejected)."""
    with pytest.raises(ValidationError):
        SOSCreate(**_valid_sos_data(tourist_id=0))


def test_negative_tourist_id_rejected():
    """Negative tourist_id is rejected."""
    with pytest.raises(ValidationError):
        SOSCreate(**_valid_sos_data(tourist_id=-1))


def test_sos_create_does_not_accept_status():
    """The client must not be able to set `status` — only the server sets it."""
    with pytest.raises(ValidationError):
        SOSCreate(**_valid_sos_data(status="resolved"))


def test_sos_boundary_coordinates_accepted():
    """Boundary coordinate values (-90/90, -180/180) are accepted."""
    SOSCreate(**_valid_sos_data(latitude=-90.0, longitude=-180.0))
    SOSCreate(**_valid_sos_data(latitude=90.0, longitude=180.0))


def test_sos_boundary_tourist_id_accepted():
    """tourist_id=1 (minimum valid) is accepted."""
    sos = SOSCreate(**_valid_sos_data(tourist_id=1))
    assert sos.tourist_id == 1"""
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models.incident import SOSEvent
from app.models.tourist import Tourist

client = TestClient(app)


def _register_tourist(name="SOS Tester", phone="9876511111"):
    """Helper: register a tourist via the API and return the created tourist dict."""
    resp = client.post("/api/register", json={"name": name, "phone": phone})
    assert resp.status_code == status.HTTP_201_CREATED
    return resp.json()


def test_valid_sos_returns_201():
    """POST /api/sos with a valid existing tourist returns 201."""
    tourist = _register_tourist()
    resp = client.post("/api/sos", json={
        "tourist_id": tourist["id"],
        "latitude": 16.5044,
        "longitude": 80.4101,
    })
    assert resp.status_code == status.HTTP_201_CREATED
    body = resp.json()
    assert body["tourist_id"] == tourist["id"]
    assert body["latitude"] == 16.5044
    assert body["longitude"] == 80.4101
    assert body["status"] == "active"
    assert "id" in body
    assert "created_at" in body


def test_sos_is_persisted():
    """An SOS event is visible in the database after creation."""
    tourist = _register_tourist()
    client.post("/api/sos", json={
        "tourist_id": tourist["id"],
        "latitude": 16.5044,
        "longitude": 80.4101,
    })
    db = SessionLocal()
    try:
        row = db.execute(
            db.query(SOSEvent).filter(SOSEvent.tourist_id == tourist["id"]).statement
        ).fetchone()
        assert row is not None
    finally:
        db.close()

    # Use a direct query instead
    db = SessionLocal()
    try:
        events = db.query(SOSEvent).filter(SOSEvent.tourist_id == tourist["id"]).all()
        assert len(events) >= 1
        assert events[-1].latitude == 16.5044
    finally:
        db.close()


def test_unknown_tourist_returns_404():
    """POST /api/sos with a non-existent tourist_id returns 404."""
    resp = client.post("/api/sos", json={
        "tourist_id": 999999,
        "latitude": 16.5044,
        "longitude": 80.4101,
    })
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_invalid_latitude_returns_422():
    """Latitude outside [-90, 90] is rejected with 422."""
    tourist = _register_tourist()
    resp = client.post("/api/sos", json={
        "tourist_id": tourist["id"],
        "latitude": 95.0,
        "longitude": 80.0,
    })
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_invalid_longitude_returns_422():
    """Longitude outside [-180, 180] is rejected with 422."""
    tourist = _register_tourist()
    resp = client.post("/api/sos", json={
        "tourist_id": tourist["id"],
        "latitude": 16.5,
        "longitude": 200.0,
    })
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_get_sos_returns_stored_events():
    """GET /api/sos returns all stored SOS events."""
    tourist = _register_tourist()
    client.post("/api/sos", json={
        "tourist_id": tourist["id"],
        "latitude": 16.5044,
        "longitude": 80.4101,
    })
    resp = client.get("/api/sos")
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert "sos_events" in body
    assert isinstance(body["sos_events"], list)
    assert any(
        e["tourist_id"] == tourist["id"] and e["latitude"] == 16.5044
        for e in body["sos_events"]
    )