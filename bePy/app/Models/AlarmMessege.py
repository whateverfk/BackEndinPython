from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class AlarmMessage(Base):
    __tablename__ = "alarm_messages"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    device_id = Column(
        Integer,
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    channel_id_in_device = Column(String(32), nullable=True, index=True)
    channel_name = Column(String(255), nullable=True)
    event = Column(String(64), nullable=True, index=True)

    message = Column(Text, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # relationships
    owner = relationship("User", back_populates="alarm_messages")

    __table_args__ = (
        Index(
            "idx_alarm_user_created_at",
            "user_id",
            created_at.desc()
        ),
    )
