"""Tests for the tourist POST /api/register endpoint."""
import os
import sqlite3

from fastapi import status
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_successful_registration_returns_201():
    """A valid tourist should be created and return 201."""
    response = client.post(
        "/api/register",
        json={"name": "Rahul Kumar", "phone": "9876543210"},
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_response_contains_tourist_id():
    """The 201 response body must contain an integer id."""
    response = client.post(
        "/api/register",
        json={"name": "Anjali", "phone": "9810000000"},
    )
    body = response.json()
    assert "id" in body
    assert isinstance(body["id"], int)
    assert body["id"] > 0


def test_name_and_phone_returned_correctly():
    """Returned name is trimmed and phone is normalized to 10 digits."""
    response = client.post(
        "/api/register",
        json={"name": "  Vikram  ", "phone": "91-9876543210"},
    )
    body = response.json()
    assert body["name"] == "Vikram"
    assert body["phone"] == "9876543210"


def test_invalid_phone_returns_422():
    """A short / malformed phone number must be rejected with 422."""
    response = client.post(
        "/api/register",
        json={"name": "Bad Phone", "phone": "123"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_missing_name_returns_422():
    """Omitting the required name field must be rejected with 422."""
    response = client.post(
        "/api/register",
        json={"phone": "9876543210"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_duplicate_phone_returns_409():
    """Registering the same phone a second time must return 409 Conflict."""
    payload = {"name": "Duplicate", "phone": "9999999999"}
    first = client.post("/api/register", json=payload)
    assert first.status_code == status.HTTP_201_CREATED

    second = client.post("/api/register", json=payload)
    assert second.status_code == status.HTTP_409_CONFLICT


def test_tourist_persisted_in_sqlite():
    """The created tourist must be visible in the SQLite database file."""
    response = client.post(
        "/api/register",
        json={"name": "Persisted", "phone": "9000000000"},
    )
    assert response.status_code == status.HTTP_201_CREATED

    db_path = os.environ["TEST_DB_PATH"]
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT name, phone FROM tourists WHERE phone = ?",
            ("9000000000",),
        ).fetchone()

    assert row is not None
    assert row[0] == "Persisted"
    assert row[1] == "9000000000"
