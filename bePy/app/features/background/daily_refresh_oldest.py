import asyncio
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.Models.user import User
from app.Models.device import Device
from app.features.background.update_data_record import refresh_device_oldest_records

async def daily_refresh_oldest():
    print("=== Start daily refresh oldest_record_date for all devices ===")

    db: Session = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()

        for user in users:
            devices = db.query(Device).filter(
                Device.owner_superadmin_id == user.id
            ).all()

            print(f"Refresh oldest for user name = {user.username}")

            for device in devices:
                await refresh_device_oldest_records(db, device)
                db.commit()   # commit theo device

        print("=== Daily refresh oldest completed ===")

    except Exception as e:
        db.rollback()
        print("Error in daily refresh oldest:", e)

    finally:
        db.close()
