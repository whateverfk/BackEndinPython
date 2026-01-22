from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional

from app.Models.device import Device
from app.Models.channel import Channel
from app.Models.device_user import DeviceUser
from app.core.exceptions import DeviceNotFoundError, ChannelNotFoundError, UserNotFoundError


async def get_device_or_404(
    db: AsyncSession,
    device_id: int,
    owner_superadmin_id: Optional[str] = None
) -> Device:
    """
    Get device by ID, optionally filtered by owner superadmin.
    """
    query = select(Device).where(Device.id == device_id)
    
    if owner_superadmin_id is not None:
        query = query.where(Device.owner_superadmin_id == owner_superadmin_id)
    
    result = await db.execute(query)
    device = result.scalars().first()
    
    if not device:
        raise DeviceNotFoundError()
    
    return device


async def get_channel_or_404(
    db: AsyncSession,
    channel_id: int,
    device_id: Optional[int] = None,
    load_details: bool = False,
    load_device: bool = False,
) -> Channel:
    """
    Get channel by ID, optionally filtered by device.
    """
    query = select(Channel).where(Channel.id == channel_id)
    
    if device_id is not None:
        query = query.where(Channel.device_id == device_id)

    if load_details:
        query = query.options(
            selectinload(Channel.extension),
            selectinload(Channel.stream_config)
        )

    if load_device:
        query = query.options(selectinload(Channel.device))
    
    result = await db.execute(query)
    channel = result.scalars().first()
    
    if not channel:
        raise ChannelNotFoundError()
    
    return channel


async def get_device_user_or_404(
    db: AsyncSession,
    device_user_id: int,
    device_id: Optional[int] = None,
    load_device: bool = False
) -> DeviceUser:
    """
    Get device user by ID, optionally filtered by device.
    """
    query = select(DeviceUser).where(DeviceUser.id == device_user_id)
    
    if device_id is not None:
        query = query.where(DeviceUser.device_id == device_id)
        
    if load_device:
        query = query.options(selectinload(DeviceUser.device))
        
    result = await db.execute(query)
    user = result.scalars().first()
    
    if not user:
        raise UserNotFoundError()
        
    return user


async def get_active_devices(db: AsyncSession, owner_superadmin_id: str) -> list[Device]:
    """
    Get all active (checked) devices for a superadmin.
    """
    result = await db.execute(select(Device).where(
        Device.owner_superadmin_id == owner_superadmin_id,
        Device.is_checked == True
    ))
    return result.scalars().all()


async def get_all_devices(db: AsyncSession, owner_superadmin_id: str) -> list[Device]:
    """
    Get all devices for a superadmin.
    """
    result = await db.execute(select(Device).where(
        Device.owner_superadmin_id == owner_superadmin_id
    ))
    return result.scalars().all()


async def get_device_channels(db: AsyncSession, device_id: int) -> list[Channel]:
    """
    Get all channels for a device.
    """
    result = await db.execute(select(Channel).where(
        Channel.device_id == device_id
    ))
    return result.scalars().all()


async def device_exists(
    db: AsyncSession,
    ip_web: str,
    owner_superadmin_id: str
) -> bool:
    """
    Check if a device with given IP already exists for a superadmin.
    """
    result = await db.execute(select(Device).where(
        Device.ip_web == ip_web,
        Device.owner_superadmin_id == owner_superadmin_id
    ))
    exists = result.scalars().first()
    
    return exists is not None
