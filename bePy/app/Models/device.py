from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import uuid
from app.Models.channel import Channel

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)

    ip_nvr = Column(String(50))
    ip_web = Column(String(50), index=True)

    username = Column(String(50))
    password = Column(String(100))

    brand = Column(String(50))
    is_checked = Column(Boolean, default=False)

    #  OWNER – GÁN TỪ TOKEN
    owner_superadmin_id = Column(
        UUID(as_uuid=True),
        index=True,
        
        nullable=True
    )
    users = relationship("DeviceUser", back_populates="device")

    channels = relationship(
        "Channel",
        cascade="all, delete-orphan",
        backref="device"
    )