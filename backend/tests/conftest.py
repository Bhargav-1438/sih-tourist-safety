"""Pytest configuration shared by all tests.

Runs before any test module is imported so the application picks up a
throwaway test database instead of the development database.
"""
import os
import shutil
import tempfile

import pytest

# ---------------------------------------------------------------------------
# Point the application at an isolated SQLite file BEFORE app modules import.
# ---------------------------------------------------------------------------
_TEST_DIR = tempfile.mkdtemp(prefix="sih_ts_test_")
TEST_DB_PATH = os.path.join(_TEST_DIR, "test_tourist_safety.db")

# SQLAlchemy sqlite URLs use forward slashes (portable across OS).
os.environ["DATABASE_URL"] = "sqlite:///" + TEST_DB_PATH.replace("\\", "/")
os.environ["TEST_DB_PATH"] = TEST_DB_PATH
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("DEBUG", "false")

# Importing the app's database + model modules registers the tables with
# Base.metadata. We create them explicitly so tests do not depend on the
# application's lifespan event running inside TestClient.
from sqlalchemy import delete  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models.tourist import Tourist  # noqa: E402
from app.models.incident import Incident, SOSEvent  # noqa: E402

Base.metadata.create_all(bind=engine)

# Provide a stable JWT secret for tests (never log it). The application reads
# its real value from the environment at import time, so this must be set before
# app.security is imported.
os.environ.setdefault("JWT_SECRET_KEY", "test-only-jwt-secret-not-for-production")


@pytest.fixture(autouse=True)
def _isolate_tourists():
    """Ensure each test starts with an empty tourists table."""
    db = SessionLocal()
    db.execute(delete(Tourist))
    db.commit()
    db.close()
    yield


@pytest.fixture(scope="session", autouse=True)
def _remove_test_db_directory():
    """Delete the temporary test database directory at the end of the session."""
    yield
    shutil.rmtree(_TEST_DIR, ignore_errors=True)
