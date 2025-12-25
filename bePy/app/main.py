from fastapi import FastAPI
from app.routers import api_router
from app.db.session import engine
from app.db.base import Base
from fastapi.middleware.cors import CORSMiddleware
from app.features.sync.auto_sync import sync_background_worker 
import asyncio
from contextlib import asynccontextmanager
from app.features.background.scheduler import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    # task = asyncio.create_task(sync_background_worker())
    # start_scheduler()
    # print("AUTO SYNC ( time and data ) STARTED")

    # để test nên tạm bỏ sync time 
    start_scheduler()
    print("AUTO SYNC (  data ) STARTED")

    yield
    stop_scheduler()
    #task.cancel()
    #try:
    #     await task
    # except asyncio.CancelledError:
    #     print(" AUTO SYNC CANCELLED")

#app = FastAPI()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # hoặc ["http://localhost:5500"] 
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép OPTIONS
    allow_headers=["*"],
)




app.include_router(api_router)
