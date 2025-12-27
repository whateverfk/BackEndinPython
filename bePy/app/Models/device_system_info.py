from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.db.base import Base


class DeviceSystemInfo(Base):
    __tablename__ = "device_system_info"

    device_id = Column(
        Integer, ForeignKey("devices.id", ondelete="CASCADE"),
        primary_key=True
    )

    model = Column(String(100))
    
    serial_number = Column(String(100))
    #firmware_version = Firmware version + Firmware release date
    firmware_version = Column(String(50))

    mac_address = Column(String(50))

