import uuid
from sqlalchemy import (
    Column, String, Boolean, DateTime
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    role = Column(String(20), default="SuperAdmin")

    owner_superadmin_id = Column(UUID(as_uuid=True), nullable=True)
    created_by_user_id = Column(UUID(as_uuid=True), nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
