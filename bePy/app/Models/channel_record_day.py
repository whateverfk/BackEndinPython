# app/models/channel_record_day.py
from sqlalchemy import Column, Integer, Date, Boolean, ForeignKey, Index

from sqlalchemy.orm import relationship
from app.db.base import Base

class ChannelRecordDay(Base):
    __tablename__ = "channel_record_days"

    id = Column(Integer, primary_key=True)

    channel_id = Column(
        Integer,
        ForeignKey("channels.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    record_date = Column(Date, nullable=False)
    has_record = Column(Boolean, default=True)

    channel = relationship(
        "Channel",
        back_populates="record_days"
    )

    __table_args__ = (
        Index(
            "ix_channel_record_day_unique",
            "channel_id",
            "record_date",
            unique=True
        ),
    )
