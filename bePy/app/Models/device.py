from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import uuid

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
