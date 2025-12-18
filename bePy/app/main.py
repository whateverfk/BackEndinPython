from fastapi import FastAPI
from app.routers import api_router
from app.db.session import engine
from app.db.base import Base
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # hoặc ["http://localhost:5500"] 
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép OPTIONS
    allow_headers=["*"],
)

# tạo bảng
Base.metadata.create_all(bind=engine)

app.include_router(api_router)
