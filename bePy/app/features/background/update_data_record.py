import asyncio
import datetime
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.Models.device import Device
from app.features.RecordInfo.hikrecord import HikRecordService

async def auto_sync_all_devices():
    db: Session = SessionLocal()
    print(
        f"[SCHEDULER] Job triggered at {datetime.datetime.now()}"
    )

    try:
        devices = db.query(Device).filter(
            Device.is_checked == True
        ).all()
        record_service = HikRecordService()
        for device in devices:
            try:
                await record_service.sync_device_channels_data_core(
                    db=db,
                    device=device
                )
                db.commit()
            except Exception as e:
                db.rollback()
                print(f"[SYNC ERROR] Device {device.id}: {e}")

    finally:
        db.close()

