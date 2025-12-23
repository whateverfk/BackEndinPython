from fastapi import FastAPI
from app.routers import api_router
from app.db.session import engine
from app.db.base import Base
from fastapi.middleware.cors import CORSMiddleware
from app.features.sync.auto_sync import sync_background_worker 
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    task = asyncio.create_task(sync_background_worker())
    print("AUTO SYNC STARTED")

    yield

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print(" AUTO SYNC CANCELLED")

app = FastAPI(lifespan=lifespan)

#app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # hoặc ["http://localhost:5500"] 
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép OPTIONS
    allow_headers=["*"],
)




app.include_router(api_router)
