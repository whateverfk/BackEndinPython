from sqlalchemy import Column, Integer, String, Boolean, DateTime,ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.base import Base
from sqlalchemy.orm import relationship

class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, nullable=False)
    ip = Column(String, nullable=False)
    sync_time = Column(DateTime, server_default=func.now())
    is_success = Column(Boolean, default=False)
    message = Column(String)

    owner_superadmin_id = Column(UUID(as_uuid=True), nullable=False)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)  # Foreign key to User

    # Relationship with User
    owner = relationship(
        "User",
        back_populates="sync_logs",  # Removed 'delete-orphan' here to avoid conflict
        
    )