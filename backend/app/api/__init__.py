"""API router package.

Endpoint groups live under this router and are included by the main
application. Currently exposes the tourist registration routes.
"""
from fastapi import APIRouter

from app.api.tourist import router as tourist_router

api_router = APIRouter()
api_router.include_router(tourist_router)

