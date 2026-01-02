import asyncio
from app.db.session import SessionLocal
from app.Models.device import Device
from app.features.RecordInfo.hikrecord import HikRecordService


async def trigger_device_init_data(device_id: int):
    db = SessionLocal()
    try:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            return

        record_service = HikRecordService()
        print("start init")
        await record_service.device_channels_init_data(db, device)

        db.commit() 
        print("Init done ????")  
    except Exception as e:
        db.rollback()
        print("[AUTO SYNC ERROR]", e)
        raise
    finally:
        db.close()
