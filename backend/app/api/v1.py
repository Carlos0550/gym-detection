"""API v1: agrupa todos los routers bajo el prefijo /api/v1."""

from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.gyms.router import router as gyms_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(gyms_router)
