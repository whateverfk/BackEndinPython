from sqlalchemy import Column, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class SyncSetting(Base):
    __tablename__ = "sync_settings"

    id = Column(Integer, primary_key=True)
    is_enabled = Column(Boolean, default=False)
    interval_minutes = Column(Integer, default=1)

    owner_superadmin_id = Column(UUID(as_uuid=True), nullable=False)
    owner = relationship("User", backref="sync_settings", cascade="all, delete-orphan")