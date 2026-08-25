"""API router package.

Endpoint groups live under this router and are included by the main
application. Currently exposes registration and digital-ID routes.
"""
from fastapi import APIRouter

from app.api.tourist import router as tourist_router
from app.api.digital_id import router as digital_id_router

api_router = APIRouter()
api_router.include_router(tourist_router)
api_router.include_router(digital_id_router)


