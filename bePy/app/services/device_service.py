from sqlalchemy.orm import Session
from typing import Optional

from app.Models.device import Device
from app.Models.channel import Channel
from app.Models.device_user import DeviceUser
from app.core.exceptions import DeviceNotFoundError, ChannelNotFoundError, UserNotFoundError


def get_device_or_404(
    db: Session,
    device_id: int,
    owner_superadmin_id: Optional[str] = None
) -> Device:
    """
    Get device by ID, optionally filtered by owner superadmin.
    """
    query = db.query(Device).filter(Device.id == device_id)
    
    if owner_superadmin_id is not None:
        query = query.filter(Device.owner_superadmin_id == owner_superadmin_id)
    
    device = query.first()
    
    if not device:
        raise DeviceNotFoundError()
    
    return device


def get_channel_or_404(
    db: Session,
    channel_id: int,
    device_id: Optional[int] = None
) -> Channel:
    """
    Get channel by ID, optionally filtered by device.
    """
    query = db.query(Channel).filter(Channel.id == channel_id)
    
    if device_id is not None:
        query = query.filter(Channel.device_id == device_id)
    
    channel = query.first()
    
    if not channel:
        raise ChannelNotFoundError()
    
    return channel


def get_device_user_or_404(
    db: Session,
    device_user_id: int,
    device_id: Optional[int] = None
) -> DeviceUser:
    """
    Get device user by ID, optionally filtered by device.
    """
    query = db.query(DeviceUser).filter(DeviceUser.id == device_user_id)
    
    if device_id is not None:
        query = query.filter(DeviceUser.device_id == device_id)
        
    user = query.first()
    
    if not user:
        raise UserNotFoundError()
        
    return user


def get_active_devices(db: Session, owner_superadmin_id: str) -> list[Device]:
    """
    Get all active (checked) devices for a superadmin.
    """
    return db.query(Device).filter(
        Device.owner_superadmin_id == owner_superadmin_id,
        Device.is_checked == True
    ).all()


def get_all_devices(db: Session, owner_superadmin_id: str) -> list[Device]:
    """
    Get all devices for a superadmin.
    """
    return db.query(Device).filter(
        Device.owner_superadmin_id == owner_superadmin_id
    ).all()


def get_device_channels(db: Session, device_id: int) -> list[Channel]:
    """
    Get all channels for a device.
    """
    return db.query(Channel).filter(
        Channel.device_id == device_id
    ).all()


def device_exists(
    db: Session,
    ip_web: str,
    owner_superadmin_id: str
) -> bool:
    """
    Check if a device with given IP already exists for a superadmin.
    """
    exists = db.query(Device).filter(
        Device.ip_web == ip_web,
        Device.owner_superadmin_id == owner_superadmin_id
    ).first()
    
    return exists is not None
