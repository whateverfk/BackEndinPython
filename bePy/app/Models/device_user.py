from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey,Index
from sqlalchemy.orm import relationship
from app.db.base import Base
from sqlalchemy import UniqueConstraint

class DeviceUser(Base):
    __tablename__ = "device_users"

    id = Column(Integer, primary_key=True)

    device_id = Column(
        Integer,
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False
    )

    user_id = Column(Integer)  # ID từ thiết bị (ISAPI)
    user_name = Column(String(50))
    role = Column(String(20)) #adminsta
    is_active = Column(Boolean, default=True)
    device = relationship(
        "Device",
        back_populates="users"
    )
    __table_args__ = (
        UniqueConstraint(
            "device_id", "user_id",
            name="uq_device_user"
        ),
    )
