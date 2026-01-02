from sqlalchemy import Column, Integer, Boolean, ForeignKey,UUID,String
from sqlalchemy.orm import relationship
from app.db.base import Base

class SyncSetting(Base):
    __tablename__ = "sync_settings"

    id = Column(Integer, primary_key=True)
    is_enabled = Column(Boolean, default=False)
    interval_minutes = Column(Integer, default=1)

    owner_superadmin_id = Column(UUID(as_uuid=True), nullable=False)

    owner_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True
    )

    owner = relationship(
        "User",
        back_populates="sync_settings"
    )
