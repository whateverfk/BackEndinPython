from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import uuid
from app.Models.channel import Channel
from app.Models.device_system_info import DeviceSystemInfo
from app.Models.device_user import DeviceUser

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
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=True
    )

    users = relationship("DeviceUser", back_populates="device")
    
    system_info = relationship(
        "DeviceSystemInfo", uselist=False, cascade="all, delete-orphan"
    )

    channels = relationship(
        "Channel",
        cascade="all, delete-orphan",
        backref="device"
    )