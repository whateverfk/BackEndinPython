from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.Models.device import Device
from app.Models.device_system_info import DeviceSystemInfo
from app.features.GetDevicesDetail.HikDetailService import HikDetailService
from app.features.RecordInfo.deps import build_hik_auth
from app.features.GetDevicesDetail.WorkWithDb import upsert_device_storage,get_device_storage_from_db

router = APIRouter(
    prefix="/api/device/{id}/infor",
    tags=["Devices_info"]
)



@router.get("")
async def get_device_system_info(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(DeviceSystemInfo).where(
        DeviceSystemInfo.device_id == id
    )

    result =  db.execute(stmt)
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
    stmt = select(Device).where(Device.id == id)
    result =  db.execute(stmt)
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
    stmt = select(DeviceSystemInfo).where(
        DeviceSystemInfo.device_id == id
    )
    result =  db.execute(stmt)
    obj = result.scalar_one_or_none()

    if obj:
        obj.model = system_info["model"]
        obj.serial_number = system_info["serial_number"]
        obj.firmware_version = system_info["firmware_version"]
        obj.mac_address = system_info["mac_address"]
    else:
        obj = DeviceSystemInfo(
            device_id=id,
            **system_info
        )
        db.add(obj)

    db.commit()

    return {
        "status": "ok",
        "source": "device",
        "data": system_info
    }



@router.post("/storage")
async def sync_device_storage(
    id: int,
    db: AsyncSession = Depends(get_db),
):
    device = db.get(Device,id)
    headers = build_hik_auth(device)
    hikservice = HikDetailService()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    storage_data = await hikservice.get_device_storage(device, headers)

    if not storage_data:
        raise HTTPException(status_code=502, detail="Cannot fetch storage from device")

    await upsert_device_storage(db, device.id, storage_data)

    return {
        "status": "success",
        "count": len(storage_data)
    }

@router.get("/storage")
async def get_device_storage(
    id: int,
    db: AsyncSession = Depends(get_db),
):
    data = await get_device_storage_from_db(db, id)

    return [
        {
            "hdd_id": d.hdd_id,
            "hdd_name": d.hdd_name,
            "status": d.status,
            "hdd_type": d.hdd_type,
            "capacity": d.capacity,
            "free_space": d.free_space,
            "property": d.property,
        }
        for d in data
    ]
