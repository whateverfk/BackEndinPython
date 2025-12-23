import asyncio
import traceback
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.Models.sync_setting import SyncSetting
from app.features.sync.engine import SyncEngine

_is_running = False
running_tasks = {}  # This will store the tasks for each owner_id

async def sync_for_superadmin(owner_id: int, interval_minutes: int):
    engine = SyncEngine()

    while True:
        db = SessionLocal()
        try:

            await engine.sync_by_superadmin(db, owner_id)
            print(f"Auto sync completed for owner_superadmin_id: {owner_id}")
        finally:
            db.close()

        await asyncio.sleep(interval_minutes * 60)

async def sync_background_worker():
    while True:
        db = SessionLocal()
        try:
            settings = db.query(SyncSetting).filter(
                SyncSetting.is_enabled == True
            ).all()

            active_owner_ids = set()

            for setting in settings:
                owner_id = setting.owner_superadmin_id
                active_owner_ids.add(owner_id)

                if owner_id not in running_tasks or running_tasks[owner_id].done():
                    running_tasks[owner_id] = asyncio.create_task(
                        sync_for_superadmin(
                            owner_id,
                            setting.interval_minutes or 10
                        )
                    )
                    print(f"Started auto sync for owner_superadmin_id: {owner_id}")

            # cancel worker bị disable aka dừng worker của admin bị xóa khỏi db 
            for owner_id in list(running_tasks.keys()):
                if owner_id not in active_owner_ids:
                    running_tasks[owner_id].cancel()
                    del running_tasks[owner_id]

        finally:
            db.close()

        await asyncio.sleep(30)
