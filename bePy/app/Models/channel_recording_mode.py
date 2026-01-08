from sqlalchemy import Column, Integer, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.Models.recording_mode_enum_class import RecordingMode


class ChannelRecordingMode(Base):
    __tablename__ = "channel_recordings_mode"

    id = Column(Integer, primary_key=True)

    channel_id = Column(
        Integer,
        ForeignKey("channels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True
    )

    default_mode = Column(
        Enum(RecordingMode),
        nullable=False
    )

    schedule_enabled = Column(Boolean, default=True)

    # relationship
    channel = relationship(
        "Channel",
        back_populates="recording"
    )
