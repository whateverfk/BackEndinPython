from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.Models.device import Device
from app.Models.device_system_info import DeviceSystemInfo
from app.features.GetDevicesDetail import HikDetailService
from app.features.RecordInfo.deps import build_hik_auth

router = APIRouter(
    prefix="/api/device/{id}/infor",
    tags=["Devices_info"]
)

@router.get("")
async def get_device_system_info(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(DeviceSystemInfo).where(
            DeviceSystemInfo.device_id == id
        )
    )
    info = result.scalar_one_or_none()

    if not info:
        raise HTTPException(
            status_code=404,
            detail="System info not found, please sync first"
        )

    return {
        "device_id": info.device_id,
        "model": info.model,
        "serial_number": info.serial_number,
        "firmware_version": info.firmware_version,
        "mac_address": info.mac_address
    }

@router.post("/sync")
async def sync_device_system_info(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    # 1. Lấy device
    result = await db.execute(
        select(Device).where(Device.id == id)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # 2. Build auth header
    headers = build_hik_auth(device)

    # 3. Gọi ISAPI
    hikservice = HikDetailService()
    system_info = await hikservice.getSystemInfo(device, headers)
    if not system_info:
        raise HTTPException(
            status_code=502,
            detail="Failed to fetch system info from device"
        )

    # 4. Upsert DB
    result = await db.execute(
        select(DeviceSystemInfo).where(
            DeviceSystemInfo.device_id == id
        )
    )
    obj = result.scalar_one_or_none()

    if obj:
        obj.model = system_info["model"]
        obj.serial_number = system_info["serial_number"]
        obj.firmware_version = system_info["firmware_version"]
        obj.mac_address = system_info["mac_address"]
    else:
        obj = DeviceSystemInfo(**system_info)
        db.add(obj)

    await db.commit()

    return {
        "status": "ok",
        "source": "device",
        "data": system_info
    }
