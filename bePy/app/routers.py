from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.device import router as device_router
from app.api.sync import router as sync_router
from app.api.logs import router as logs_router
from app.api.config import router as config_router
from app.api.device_sys_infor import router as device_sys_info_router
from app.api.channel_device_info import router as channel_device_info_router
from app.api.device_user import router as whatever
from app.api.device_user_permission import router as permission
from app.api.live import router as live
from app.api.channels import router as channels
from app.api.alarm import router as alarm

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(device_router)
api_router.include_router(sync_router)
api_router.include_router(logs_router)
api_router.include_router(config_router)
api_router.include_router(device_sys_info_router)
api_router.include_router(channel_device_info_router)
api_router.include_router(whatever)
api_router.include_router(permission)
api_router.include_router(live)
api_router.include_router(channels)
api_router.include_router(alarm)