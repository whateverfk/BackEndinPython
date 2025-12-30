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

    scope = Column(String(10))      # local | remote
    permission = Column(String(30)) # record | playback | preview | ptz_control

    enabled = Column(Boolean, default=False)

    __table_args__ = (
        Index(
            "ix_user_channel_permission_unique",
            "device_user_id", "channel_id", "scope", "permission",
            unique=True
        ),
    )
