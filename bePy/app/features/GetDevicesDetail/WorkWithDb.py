from sqlalchemy import select
from app.Models.device_system_info import DeviceSystemInfo

async def saveSystemInfo(db, system_info: dict):
    stmt = select(DeviceSystemInfo).where(
        DeviceSystemInfo.device_id == system_info["device_id"]
    )
    result =  db.execute(stmt)
    obj = result.scalar_one_or_none()

    if obj:
        # update
        obj.model = system_info["model"]
        obj.serial_number = system_info["serial_number"]
        obj.firmware_version = system_info["firmware_version"]
        obj.mac_address = system_info["mac_address"]
    else:
        # insert
        obj = DeviceSystemInfo(**system_info)
        db.add(obj)

    await db.commit()
