"""
SIH Tourist Safety - Backend API.

Minimal FastAPI application for the prototype foundation.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import (
    DEBUG,
    ENVIRONMENT,
    PROJECT_DESCRIPTION,
    PROJECT_NAME,
    PROJECT_VERSION,
)
from app.database import Base, engine

# Importing the models registers their tables with Base.metadata so that the
# table-creation step in lifespan() (and in tests) has them available.
from app.models import Tourist  # noqa: F401
from app.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables on startup. No migrations are used for this
    # one-day prototype; tables are derived from the model definitions.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=PROJECT_NAME,
    description=PROJECT_DESCRIPTION,
    version=PROJECT_VERSION,
    debug=DEBUG,
    lifespan=lifespan,
)

# CORS: allow only the local Vite dev server during development so the
# frontend can call the API while it is being built. Production origins will
# be configured explicitly later.
if ENVIRONMENT == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
    "http://localhost:5173",
    "https://sih-tourist-safety-1.onrender.com",
],  # Vite dev server
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include the API router (currently exposes tourist registration) under /api.
app.include_router(api_router, prefix="/api")


@app.get("/health", tags=["health"])
def health_check() -> dict:
    """Liveness check. Does not touch the database or require auth."""
    return {"status": "ok"}

