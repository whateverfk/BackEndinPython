from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base
from sqlalchemy import Index

class UserGlobalPermission(Base):
    __tablename__ = "user_global_permissions"

    id = Column(Integer, primary_key=True)

    device_user_id = Column(
        Integer, ForeignKey("device_users.id", ondelete="CASCADE"),
        nullable=False
    )

    scope = Column(String(10), nullable=False)  # local | remote

    # ===== common =====
    upgrade = Column(Boolean, default=False)
    parameter_config = Column(Boolean, default=False)
    restart_or_shutdown = Column(Boolean, default=False)
    log_or_state_check = Column(Boolean, default=False)
    manage_channel = Column(Boolean, default=False)

    # ===== local =====
    playback = Column(Boolean, default=False)
    record = Column(Boolean, default=False)
    backup = Column(Boolean, default=False)

    # ===== remote =====
    preview = Column(Boolean, default=False)
    voice_talk = Column(Boolean, default=False)
    alarm_out_or_upload = Column(Boolean, default=False)
    control_local_out = Column(Boolean, default=False)
    transparent_channel = Column(Boolean, default=False)

    __table_args__ = (
        Index(
            "ix_user_global_permission_user_scope",
            "device_user_id", "scope",
            unique=True
        ),
    )
