from sqlalchemy import Column, Integer, Time, SmallInteger, ForeignKey, Enum, Index
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.Models.recording_mode_enum_class import RecordingMode
class ChannelRecordingModeTimeline(Base):
    __tablename__ = "channel_recording_mode_timeline"

    id = Column(Integer, primary_key=True)

    channel_id = Column(
        Integer,
        ForeignKey("channels.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 0 = Monday ... 6 = Sunday
    day_of_week = Column(SmallInteger, nullable=False)

    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    mode = Column(
        Enum(RecordingMode),
        nullable=False
    )

    # relationship
    channel = relationship(
        "Channel",
        back_populates="recording_timeline"
    )

    __table_args__ = (
        Index(
            "ix_channel_day_time",
            "channel_id",
            "day_of_week",
            "start_time"
        ),
    )
