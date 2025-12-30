from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class UserGlobalPermission(Base):
    __tablename__ = "user_global_permissions"

    id = Column(Integer, primary_key=True)
    device_user_id = Column(
        Integer, ForeignKey("device_users.id", ondelete="CASCADE"),
        unique=False
    )

    scope = Column(String(10))  # local | remote

    # common
    upgrade = Column(Boolean)
    parameter_config = Column(Boolean)
    restart_or_shutdown = Column(Boolean)
    log_or_state_check = Column(Boolean)
    manage_channel = Column(Boolean)

    # local only
    playback = Column(Boolean)
    record = Column(Boolean)
    backup = Column(Boolean)

    # remote only
    preview = Column(Boolean)
    voice_talk = Column(Boolean)
    alarm_out_or_upload = Column(Boolean)
    control_local_out = Column(Boolean)
    transparent_channel = Column(Boolean)
