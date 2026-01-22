from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response
from contextlib import asynccontextmanager
import asyncio
import os
from dotenv import load_dotenv
from app.routers import api_router
from app.features.sync.auto_sync import sync_background_worker
from app.features.background.update_data_record import auto_sync_all_devices
from app.features.background.daily_refresh_oldest import daily_refresh_oldest
from app.features.background.scheduler import start_scheduler, stop_scheduler
from app.features.background.save_alarm import AlarmSupervisor
from app.core.http_client import close_http_client
from app.core.logger import setup_logger

logger = setup_logger(__name__)


class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response: Response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-store"
        return response




# =========================
# LOAD ENV
# =========================
load_dotenv()

HLS_DIR = os.getenv("HLS_DIR")
if not HLS_DIR:
    raise RuntimeError("HLS_DIR is not set in .env")

# =========================
# LIFESPAN
# =========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    supervisor = AlarmSupervisor()
    #bg auto sync time
    sync_task = asyncio.create_task(sync_background_worker())
    # Bắt alert steam
    asyncio.create_task(supervisor.run())

    # chạy sync ngay khi start
    
    # 2 cái này là cái scheduler nhưng active ngay 1 lần khi start/restart server BE 
    await auto_sync_all_devices()
    
    await daily_refresh_oldest()

    # scheduler để cập nhật data monitor mỗi /5p và cập nhật data monitor ngày cũ nhất mỗi 1h sáng 
    start_scheduler()
    logger.info("AUTO SYNC (data) STARTED")

    yield

    # shutdown
    stop_scheduler()
    await close_http_client()

    sync_task.cancel()
    try:
        await sync_task
    except asyncio.CancelledError:
        logger.info("AUTO SYNC CANCELLED")

# =========================
# APP
# =========================
app = FastAPI(lifespan=lifespan)

# =========================
# MIDDLEWARE
# =========================
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# API ROUTERS 
# =========================
app.include_router(api_router)

# =========================
# HLS STATIC
# =========================
app.mount(
    "/hls",
    StaticFiles(directory=HLS_DIR),
    name="hls",
)

# =========================
# FRONTEND STATIC
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
WWWROOT_DIR = os.path.join(BASE_DIR, "dist")

app.mount(
    "/",
    #StaticFiles(directory=WWWROOT_DIR, html=True),
    NoCacheStaticFiles(directory=WWWROOT_DIR, html=True),
    name="frontend",
)
