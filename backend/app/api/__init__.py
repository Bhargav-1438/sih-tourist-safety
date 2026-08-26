"""API router package.

Endpoint groups live under this router and are included by the main
application. Currently exposes registration, digital-ID, incident, and SOS routes.
"""
from fastapi import APIRouter

from app.api.tourist import router as tourist_router
from app.api.digital_id import router as digital_id_router
from app.api.incident import router as incident_router
from app.api.sos import router as sos_router
from app.api.risk import router as risk_router
from app.api.patrol import router as patrol_router

api_router = APIRouter()
api_router.include_router(tourist_router)
api_router.include_router(digital_id_router)
api_router.include_router(incident_router)
api_router.include_router(sos_router)
api_router.include_router(risk_router)
api_router.include_router(patrol_router)


