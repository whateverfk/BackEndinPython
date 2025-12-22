# app/models/channel_record_time_range.py
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.base import Base

class ChannelRecordTimeRange(Base):
    __tablename__ = "channel_record_time_ranges"

    id = Column(Integer, primary_key=True)

    record_day_id = Column(
        Integer,
        ForeignKey("channel_record_days.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    record_day = relationship("ChannelRecordDay", backref="time_ranges")

    __table_args__ = (
        Index("ix_record_day_time_range", "record_day_id"),
    )
