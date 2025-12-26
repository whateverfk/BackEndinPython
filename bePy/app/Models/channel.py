from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, Index, ForeignKey
from app.db.base import Base


class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"))
    channel_no = Column(Integer, nullable=False)
    name = Column(String(100))

    
    oldest_record_date = Column(Date, index=True)
    latest_record_date = Column(Date, index=True)
    last_sync_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    last_channel_sync_at = Column(DateTime, nullable=True)  
    __table_args__ = (
        Index("ix_device_channel_unique", "device_id", "channel_no", unique=True),
    )
