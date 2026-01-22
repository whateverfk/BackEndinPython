from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.Models.device import Device
from app.features.RecordInfo.hikrecord import HikRecordService
from app.core.logger import setup_logger

logger = setup_logger(__name__)


async def trigger_device_init_data(device_id: int):
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Device).where(Device.id == device_id))
            device = result.scalars().first()
            if not device:
                return

            record_service = HikRecordService()
            logger.info("start init")
            await record_service.device_channels_init_data(db, device)

            await db.commit() 
            logger.info("Init done ????")  
        except Exception as e:
            await db.rollback()
            logger.error(f"[AUTO SYNC ERROR] {e}")
            raise
