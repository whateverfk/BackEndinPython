from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.device import router as device_router


api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(device_router)