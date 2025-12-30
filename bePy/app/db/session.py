from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

# Lấy giá trị DATABASE_URL từ biến môi trường
DATABASE_URL = os.getenv("DATABASE_URL")



# nếu prod:
# postgresql://user:pass@host/db

engine = create_engine(
    DATABASE_URL,
    #connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
