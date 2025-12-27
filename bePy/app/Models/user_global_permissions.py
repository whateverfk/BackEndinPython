from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base
class UserGlobalPermission(Base):
    __tablename__ = "user_global_permissions"

    id = Column(Integer, primary_key=True)
    device_user_id = Column(
        Integer, ForeignKey("device_users.id", ondelete="CASCADE"), unique=True
    )

    scope = Column(String(10))  # local | remote

    backup = Column(Boolean)
    record = Column(Boolean)
    playback = Column(Boolean)
    preview = Column(Boolean)

    log_or_state_check = Column(Boolean)
    parameter_config = Column(Boolean)
    restart_or_shutdown = Column(Boolean)
    upgrade = Column(Boolean)

    voice_talk = Column(Boolean)
    alarm_out_or_upload = Column(Boolean)
    serial_port = Column(Boolean)
    video_out_put_control = Column(Boolean)
    manage_channel = Column(Boolean)

    user = relationship("DeviceUser", backref="global_permission")
