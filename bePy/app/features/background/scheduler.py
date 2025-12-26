from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.features.background.update_data_record  import auto_sync_all_devices

scheduler = AsyncIOScheduler(timezone="Asia/Ho_Chi_Minh")

def start_scheduler():
    scheduler.add_job(
        auto_sync_all_devices,
        trigger=IntervalTrigger(minutes=5),
        id="auto_sync_devices",
        replace_existing=True,
        max_instances=1,
        coalesce=True
    )
    scheduler.start()

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
