"""
Application configuration.

Settings are read from environment variables, optionally loaded from a local
``.env`` file (development only). No secrets are hard-coded in source.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# This file lives at backend/app/config.py, so two parents up is the backend/
# directory where the .env file is expected to live.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load variables from a local .env file if present. Production environments
# should supply these values directly in the environment.
load_dotenv(BASE_DIR / ".env")


def _get_bool(key: str, default: bool = False) -> bool:
    """Interpret a config value as a boolean."""
    return os.getenv(key, str(default)).strip().lower() in {"1", "true", "yes", "on"}


# --- Application ---
PROJECT_NAME: str = os.getenv("PROJECT_NAME", "SIH Tourist Safety")
PROJECT_VERSION: str = os.getenv("PROJECT_VERSION", "0.1.0")
PROJECT_DESCRIPTION: str = os.getenv(
    "PROJECT_DESCRIPTION",
    "Predictive Tourist Safety & Resource Optimization System prototype.",
)
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
DEBUG: bool = _get_bool("DEBUG", default=False)
HOST: str = os.getenv("HOST", "127.0.0.1")
PORT: int = int(os.getenv("PORT", "8000"))

# --- Database ---
# SQLite local file. ``sqlite:///./tourist_safety.db`` stores the database
# relative to the current working directory (the backend folder).
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./tourist_safety.db")

# --- JWT / Digital ID ---
# Used to sign the tourist's digital ID token. NEVER hard-code a secret here.
# In development a default is provided only for local convenience; production
# must always supply JWT_SECRET_KEY via the environment.
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-only-insecure-secret-change-me")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
# Token lifetime in hours (prototype default: 24h).
JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# --- Risk engine (DBSCAN clustering) ---
# Default neighbourhood radius (km) and core-point threshold used by
# GET /api/risk-zones. Both can be overridden per-request via query params.
RISK_EPS_KM: float = float(os.getenv("RISK_EPS_KM", "0.5"))
RISK_MIN_SAMPLES: int = int(os.getenv("RISK_MIN_SAMPLES", "4"))
