from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.db.base import Base

class DeviceStorage(Base):
    __tablename__ = "device_storage"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"))

    hdd_id = Column(Integer)
    hdd_name = Column(String(50))
    status = Column(String(20))
    hdd_type = Column(String(20))
    capacity = Column(Integer)
    free_space = Column(Integer)
    property = Column(String(10))  # RW / RO

