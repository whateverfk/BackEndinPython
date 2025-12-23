import asyncio
import traceback
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.Models.sync_setting import SyncSetting
from app.features.sync.engine import SyncEngine

_is_running = False

# Worker để đồng bộ hóa cho từng superadmin riêng biệt
async def sync_for_superadmin(db: Session, owner_id: int, interval_minutes: int):
    engine = SyncEngine()
    while True:
        print(f"Starting sync for owner: {owner_id}")
        await engine.sync_by_superadmin(db, owner_id)
        
        # Chờ theo thời gian interval_minutes trước khi tiếp tục sync lần sau
        print(f"Sync completed for owner {owner_id}. Waiting for {interval_minutes} minutes before next sync.")
        await asyncio.sleep(interval_minutes * 60)  # Thời gian chờ giữa các lần sync

async def sync_background_worker():
    global _is_running

    while True:
        if _is_running:
            await asyncio.sleep(5)
            continue

        try:
            _is_running = True
            db: Session = SessionLocal()

            try:
                # Lấy tất cả các setting đang bật
                settings = (
                    db.query(SyncSetting)
                    .filter(SyncSetting.is_enabled == True)
                    .all()
                )

                # Duyệt qua tất cả các setting để tạo worker cho mỗi superadmin
                for setting in settings:
                    owner_id = setting.owner_superadmin_id
                    interval_minutes = setting.interval_minutes if setting else 10
                    print(f"Creating sync worker for owner: {owner_id} with interval {interval_minutes} minutes")

                    # Tạo một worker bất đồng bộ cho mỗi superadmin
                    asyncio.create_task(sync_for_superadmin(db, owner_id, interval_minutes))

            finally:
                db.close()

        except asyncio.CancelledError:
            break

        except Exception as ex:
            traceback.print_exc()
            print("SYNC WORKER ERROR:", ex)
            await asyncio.sleep(30)

        finally:
            _is_running = False
