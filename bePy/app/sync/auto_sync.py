import asyncio
import traceback
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.Models.sync_setting import SyncSetting
from app.sync.engine import SyncEngine

_is_running = False


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
                # ✅ Lấy tất cả setting đang bật
                settings = (
                    db.query(SyncSetting)
                    .filter(SyncSetting.is_enabled == True)
                    .all()
                )

                engine = SyncEngine()
                # Với mỗi setting → lấy owner_superadmin_id → sync device của owner đó
                for setting in settings:
                    owner_id = setting.owner_superadmin_id
                    await engine.sync_by_superadmin(db, owner_id)

                #  Delay theo setting đầu tiên (hoặc mặc định)
                delay_minutes = settings[0].interval_minutes if settings else 10
                await asyncio.sleep(delay_minutes * 60)

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
