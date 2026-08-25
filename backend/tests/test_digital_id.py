"""Tests for the tourist digital-ID generation and verification."""
import base64
import json
import os

import jwt
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.config import JWT_ALGORITHM, JWT_SECRET_KEY
from app.main import app
from app.security import create_token

client = TestClient(app)


def _register_tourist(name="Test Tourist", phone="9876500000"):
    """Helper: register a tourist and return the created tourist dict."""
    resp = client.post("/api/register", json={"name": name, "phone": phone})
    assert resp.status_code == status.HTTP_201_CREATED
    return resp.json()


# ---------------------------------------------------------------------------
# Digital-ID generation
# ---------------------------------------------------------------------------


def test_digital_id_for_existing_tourist_returns_200():
    tourist = _register_tourist()
    resp = client.post(f"/api/digital-id/{tourist['id']}")
    assert resp.status_code == status.HTTP_200_OK


def test_digital_id_for_nonexistent_tourist_returns_404():
    resp = client.post("/api/digital-id/999999")
    assert resp.status_code == status.HTTP_404_NOT_FOUND


def test_digital_id_response_contains_jwt():
    tourist = _register_tourist()
    resp = client.post(f"/api/digital-id/{tourist['id']}")
    body = resp.json()
    token = body["token"]
    assert isinstance(token, str)
    assert token.count(".") == 2  # header.payload.signature
    assert jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])


def test_digital_id_response_contains_qr_data_url():
    tourist = _register_tourist()
    resp = client.post(f"/api/digital-id/{tourist['id']}")
    qr_code = resp.json()["qr_code"]
    assert qr_code.startswith("data:image/png;base64,")
    # The data portion must be decodable base64 PNG content.
    data = qr_code.split(",", 1)[1]
    decoded = base64.b64decode(data)
    assert decoded[:8] == b"\x89PNG\r\n\x1a\n"


def test_jwt_decodable_with_configured_secret():
    tourist = _register_tourist()
    token = client.post(f"/api/digital-id/{tourist['id']}").json()["token"]
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    assert "sub" in payload
    assert "name" in payload
    assert "exp" in payload


def test_jwt_contains_tourist_id_and_name_but_not_phone():
    tourist = _register_tourist(name="QR Person")
    token = client.post(f"/api/digital-id/{tourist['id']}").json()["token"]
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    assert payload["sub"] == str(tourist["id"])
    assert payload["name"] == "QR Person"
    assert "phone" not in payload


def test_jwt_has_expiration_claim():
    tourist = _register_tourist()
    token = client.post(f"/api/digital-id/{tourist['id']}").json()["token"]
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    assert "exp" in payload
    assert payload["exp"] > payload["iat"]


def test_digital_id_returns_tourist_id_and_expires_at():
    tourist = _register_tourist(name="Expiry Check")
    body = client.post(f"/api/digital-id/{tourist['id']}").json()
    assert body["tourist_id"] == tourist["id"]
    assert "expires_at" in body
    assert "token" in body
    assert "qr_code" in body


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------


def test_verify_id_valid_token_returns_valid_true():
    tourist = _register_tourist()
    token = client.post(f"/api/digital-id/{tourist['id']}").json()["token"]
    resp = client.post("/api/verify-id", json={"token": token})
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body["valid"] is True
    assert body["tourist"]["id"] == tourist["id"]
    assert body["tourist"]["name"] == tourist["name"]


def test_verify_id_tampered_token_fails():
    tourist = _register_tourist()
    token = client.post(f"/api/digital-id/{tourist['id']}").json()["token"]
    # Flip one character in the payload to break the signature.
    tampered = token[:-2] + ("A" if token[-2] != "A" else "B")
    resp = client.post("/api/verify-id", json={"token": tampered})
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["valid"] is False


def test_verify_id_malformed_token_fails():
    resp = client.post("/api/verify-id", json={"token": "not-a-jwt"})
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["valid"] is False


def test_verify_id_expired_token_fails():
    tourist = _register_tourist()
    token = create_token(tourist_id=tourist["id"], name=tourist["name"])
    # Re-sign an immediately-expired token.
    expired_token = jwt.encode(
        {
            "sub": str(tourist["id"]),
            "name": tourist["name"],
            "iat": 0,
            "exp": 1,
        },
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )
    resp = client.post("/api/verify-id", json={"token": expired_token})
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["valid"] is False


def test_verify_id_valid_token_for_nonexistent_tourist_fails():
    token = create_token(tourist_id=999999, name="Ghost")
    resp = client.post("/api/verify-id", json={"token": token})
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body["valid"] is False
    assert body["tourist"] is None


def test_verify_id_does_not_return_phone():
    tourist = _register_tourist()
    token = client.post(f"/api/digital-id/{tourist['id']}").json()["token"]
    body = client.post("/api/verify-id", json={"token": token}).json()
    raw = json.dumps(body)
    assert "phone" not in raw
    assert tourist["phone"] not in raw
