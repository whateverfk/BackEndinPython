import asyncio
import traceback
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.Models.sync_setting import SyncSetting
from app.features.sync.engine import SyncEngine

_is_running = False
running_tasks = {}  # This will store the tasks for each owner_id



async def sync_for_superadmin(owner_id):
    engine = SyncEngine()

    while True:
        db = SessionLocal()
        try:
            setting = (
                db.query(SyncSetting)
                .filter(
                    SyncSetting.owner_superadmin_id == owner_id,
                    SyncSetting.is_enabled == True
                )
                .first()
            )

            # Nếu bị disable hoặc bị xóa → dừng task
            if not setting:
                print(f"[AUTO SYNC] stopped for owner_superadmin_id={owner_id}")
                return

            await engine.sync_by_superadmin(db, owner_id)

            interval = setting.interval_minutes or 10
            print(
                f"[AUTO SYNC] done for owner_superadmin_id={owner_id}, "
                f"next run in {interval} minutes"
            )

        except Exception as e:
            print(f"[AUTO SYNC] error owner={owner_id}: {e}")

        finally:
            db.close()

        await asyncio.sleep(interval * 60)

async def sync_background_worker():
    while True:
        db = SessionLocal()
        try:
            settings = (
                db.query(SyncSetting)
                .filter(SyncSetting.is_enabled == True)
                .all()
            )

            active_owner_ids = {s.owner_superadmin_id for s in settings}

            # Start task mới
            for owner_id in active_owner_ids:
                if owner_id not in running_tasks:
                    running_tasks[owner_id] = asyncio.create_task(
                        sync_for_superadmin(owner_id)
                    )
                    print(f"[AUTO SYNC] started for owner_superadmin_id={owner_id}")

            # Cleanup task không còn setting
            for owner_id in list(running_tasks.keys()):
                if owner_id not in active_owner_ids:
                    task = running_tasks.pop(owner_id)
                    task.cancel()
                    print(f"[AUTO SYNC] cancelled for owner_superadmin_id={owner_id}")

        finally:
            db.close()

        await asyncio.sleep(30)
