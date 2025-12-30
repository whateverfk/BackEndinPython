from sqlalchemy import Column, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base
from sqlalchemy.orm import relationship

class MonitorSetting(Base):
    __tablename__ = "monitor_settings"

    id = Column(Integer, primary_key=True)
    start_day= Column(Integer, default=1)
    end_day = Column(Integer, default=31)
    order = Column(Boolean, default=False)

    owner_superadmin_id = Column(UUID(as_uuid=True), nullable=False)
    owner = relationship("User", backref="monitor_settings", cascade="all, delete-orphan")