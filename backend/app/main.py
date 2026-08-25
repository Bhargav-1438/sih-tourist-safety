"""
SIH Tourist Safety - Backend API.

A minimal FastAPI application for the prototype foundation.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.config import (
    DEBUG,
    ENVIRONMENT,
    PROJECT_DESCRIPTION,
    PROJECT_NAME,
    PROJECT_VERSION,
)

app = FastAPI(
    title=PROJECT_NAME,
    description=PROJECT_DESCRIPTION,
    version=PROJECT_VERSION,
    debug=DEBUG,
)

# CORS: allow only the local Vite dev server during development so the
# frontend can call the API while it is being built. Production origins will
# be configured explicitly later.
if ENVIRONMENT == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],  # Vite dev server
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include the (currently empty) API router under /api for future endpoints.
app.include_router(api_router, prefix="/api")


@app.get("/health", tags=["health"])
def health_check() -> dict:
    """Liveness check. Does not touch the database or require auth."""
    return {"status": "ok"}
