from sqlalchemy import Column, Integer, Boolean, ForeignKey,String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class MonitorSetting(Base):
    __tablename__ = "monitor_settings"

    id = Column(Integer, primary_key=True)
    start_day = Column(Integer, default=1)
    end_day = Column(Integer, default=31)
    order = Column(Boolean, default=False)

    owner_superadmin_id = Column(UUID(as_uuid=True), nullable=False)

    owner_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    owner = relationship(
        "User",
        back_populates="monitor_settings"
    )
