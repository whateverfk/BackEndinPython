import asyncio
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
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

    db: Session = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()

        for user in users:
            devices = db.query(Device).filter(
                Device.owner_superadmin_id == user.id
            ).all()

            logger.info(f"Refreshing oldest for user: {user.username}")

            for device in devices:
                try:
                    await refresh_device_oldest_records(db, device)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.error(f"Error refreshing device {device.id}: {e}")

        logger.info("=== Daily refresh oldest completed ===")

    except Exception as e:
        logger.error(f"Global error in daily refresh oldest: {e}")

    finally:
        db.close()

