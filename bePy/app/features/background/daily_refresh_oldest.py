import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.Models.user import User
from app.Models.device import Device
from app.features.background.update_data_record import refresh_device_oldest_records
from app.core.logger import setup_logger

logger = setup_logger(__name__)


async def daily_refresh_oldest():
    """
    Background task to refresh the oldest record date for all active devices daily.
    """
    logger.info("=== Start daily refresh oldest_record_date for all devices ===")

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(User).where(User.is_active == True))
            users = result.scalars().all()

            for user in users:
                result = await db.execute(
                    select(Device).where(Device.owner_superadmin_id == user.id)
                )
                devices = result.scalars().all()

                logger.info(f"Refreshing oldest for user: {user.username}")

                for device in devices:
                    try:
                        await refresh_device_oldest_records(db, device)
                        await db.commit()
                    except Exception as e:
                        await db.rollback()
                        logger.error(f"Error refreshing device {device.id}: {e}")

            logger.info("=== Daily refresh oldest completed ===")

        except Exception as e:
            logger.error(f"Global error in daily refresh oldest: {e}")

