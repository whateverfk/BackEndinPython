from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from app.db.base import Base

class DeviceIntegrationUser(Base):
    __tablename__ = "device_integration_users"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"))

    username = Column(String(50))
    level = Column(String(20))   # admin / operator / user
    

    is_active = Column(Boolean)
    
