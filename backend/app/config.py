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
