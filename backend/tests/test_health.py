"""Tests for the /health endpoint."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200():
    """GET /health should respond with HTTP 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_body_is_ok():
    """GET /health should return a body with status == 'ok'."""
    response = client.get("/health")
    assert response.json() == {"status": "ok"}
