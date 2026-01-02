import asyncio
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.Models.user import User
from app.Models.device import Device
from app.features.background.update_data_record import refresh_device_oldest_records

async def daily_refresh_oldest():
    """
    Job hàng ngày: refresh oldest_record_date cho tất cả channel của tất cả device
    """
    print("=== Start daily refresh oldest_record_date for all devices ===")
    db: Session = SessionLocal()
    try:
        # Lấy tất cả user
        users = db.query(User).filter(User.is_active == True).all()

        for user in users:
            # Lấy tất cả device của user
            devices = db.query(Device).filter(Device.owner_superadmin_id == user.id).all()
            
            # Chạy song song từng device
            tasks = [
                refresh_device_oldest_records(db, device)
                for device in devices
            ]
            if tasks:
                await asyncio.gather(*tasks)

        print("=== Daily refresh oldest completed ===")
    except Exception as e:
        print("Error in daily refresh oldest:", e)
    finally:
        db.close()
