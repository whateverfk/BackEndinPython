from sqlalchemy import (
    Column, Integer, String, Boolean,
    DateTime, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.base import Base

# =========================
# USER
# =========================
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

    role = Column(String, nullable=False)  # SuperAdmin | SubAdmin | User

    owner_super_admin_id = Column(UUID(as_uuid=True), nullable=True)
    created_by_user_id = Column(UUID(as_uuid=True), nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# =========================
# DEVICE
# =========================
class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True)
    ip_nvr = Column(String, nullable=False)
    ip_web = Column(String, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    brand = Column(String, nullable=False)
    is_checked = Column(Boolean, default=False)

    owner_super_admin_id = Column(UUID(as_uuid=True), nullable=True)


# =========================
# SYNC SETTING
# =========================
class SyncSetting(Base):
    __tablename__ = "sync_settings"

    id = Column(Integer, primary_key=True)
    is_enabled = Column(Boolean, default=True)
    interval_minutes = Column(Integer, default=5)

    owner_super_admin_id = Column(UUID(as_uuid=True), nullable=False)


# =========================
# SYNC LOG
# =========================
class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, nullable=False)
    ip = Column(String, nullable=False)

    sync_time = Column(DateTime(timezone=True), server_default=func.now())
    is_success = Column(Boolean, default=False)
    message = Column(String)

    owner_super_admin_id = Column(UUID(as_uuid=True), nullable=False)

    __table_args__ = (
        Index("ix_sync_logs_sync_time", "sync_time"),
    )
