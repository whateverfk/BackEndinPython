from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, Index, ForeignKey
from app.db.base import Base
from sqlalchemy.orm import relationship
from app.Models.channel_extensions import ChannelExtension
from app.Models.channel_stream_config import ChannelStreamConfig
from app.Models.device_system_info import DeviceSystemInfo

class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"))
    channel_no = Column(Integer, nullable=False)
    name = Column(String(100))

    connected_type = Column(String(20), nullable=True) 
    oldest_record_date = Column(Date, index=True)
    latest_record_date = Column(Date, index=True)
    last_sync_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    last_channel_sync_at = Column(DateTime, nullable=True)  
    extension = relationship(
        "ChannelExtension",
        uselist=False,
        back_populates="channel",
        cascade="all, delete-orphan"
    )
    stream_config = relationship(
        "ChannelStreamConfig",
        uselist=False,
        cascade="all, delete-orphan"
    )

    

    __table_args__ = (
        Index("ix_device_channel_unique", "device_id", "channel_no", unique=True),
    )

