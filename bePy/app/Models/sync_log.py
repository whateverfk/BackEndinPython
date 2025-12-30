from sqlalchemy import Column, Integer, String, Boolean, DateTime
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
    owner = relationship("User", backref="sync_logs", cascade="all, delete-orphan")