from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class DeviceUser(Base):
    __tablename__ = "device_users"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"))

    user_id = Column(Integer)              # id từ device (ISAPI)
    user_name = Column(String(50))
    role = Column(String(20))              # admin / operator / viewer

    is_active = Column(Boolean, default=True)

    device = relationship("Device", back_populates="users")
