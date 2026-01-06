from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from app.features.background.update_data_record  import auto_sync_all_devices
import asyncio
from app.features.background.daily_refresh_oldest import daily_refresh_oldest
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
    scheduler.add_job(
        daily_refresh_oldest,
        #trigger mỗi 60p
        trigger=IntervalTrigger(minutes=60),
        # trigger mỗi 1h mỗi ngày
        #trigger=CronTrigger(hour=1, minute=0),
        id="daily_refresh_oldest",
        replace_existing=True,
        max_instances=1,
        coalesce=True
    )
    scheduler.start()

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
