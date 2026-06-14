"""API v1: agrupa todos los routers bajo el prefijo /api/v1."""

from fastapi import APIRouter

from app.modules.access.router import router as access_router
from app.modules.admin.router import router as admin_router
from app.modules.auth.router import router as auth_router
from app.modules.face.router import router as face_router
from app.modules.gyms.router import router as gyms_router
from app.modules.memberships.router import router as memberships_router
from app.modules.users.router import router as users_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(gyms_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(memberships_router)
api_v1_router.include_router(face_router)
api_v1_router.include_router(access_router)
api_v1_router.include_router(admin_router)
