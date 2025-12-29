from sqlalchemy import Column, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class ChannelExtension(Base):
    __tablename__ = "channel_extensions"

    channel_id = Column(
        Integer,
        ForeignKey("channels.id", ondelete="CASCADE"),
        primary_key=True
    )

    
    motion_detect_enabled = Column(Boolean, default=False)

    channel = relationship("Channel", back_populates="extension")
