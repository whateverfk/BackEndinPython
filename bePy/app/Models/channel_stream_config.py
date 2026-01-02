from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.db.base import Base

class ChannelStreamConfig(Base):
    __tablename__ = "channel_stream_configs"

    channel_id = Column(
        Integer, ForeignKey("channels.id", ondelete="CASCADE"),
        primary_key=True
    )

    resolution_width = Column(Integer)
    resolution_height = Column(Integer)
    video_codec = Column(String(20))
    max_frame_rate = Column(Integer)

    vbr_average_cap = Column(Integer)
    fixed_quality = Column(Integer)

