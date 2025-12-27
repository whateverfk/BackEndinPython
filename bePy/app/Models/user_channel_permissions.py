from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base
from sqlalchemy import Index
class UserChannelPermission(Base):
    __tablename__ = "user_channel_permissions"

    id = Column(Integer, primary_key=True)

    device_user_id = Column(
        Integer, ForeignKey("device_users.id", ondelete="CASCADE")
    )
    channel_id = Column(
        Integer, ForeignKey("channels.id", ondelete="CASCADE")
    )

    scope = Column(String(10))   # local | remote

    preview = Column(Boolean)
    playback = Column(Boolean)
    record = Column(Boolean)
    backup = Column(Boolean)
    ptz_control = Column(Boolean)

    user = relationship("DeviceUser")
    channel = relationship("Channel")
    __table_args__ = (Index("ix_user_channel_permission_device_user_channel", "device_user_id", "channel_id"),
)

