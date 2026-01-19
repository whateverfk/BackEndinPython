import asyncio
from sqlalchemy import select
from app.features.alarm_nofi.alarm import get_alarm, build_alarm_message, send_alarm_to_n8n_webhook,save_alarm_message_async
from app.Models.device import Device
from app.features.deps import build_hik_auth
from app.db.session import AsyncSessionLocal
from app.Models.user import User
from app.core.logger import setup_logger

logger = setup_logger(__name__)


class AlarmSupervisor:
    """
    Supervisor to manage background alarm listener tasks for each device.
    """
    def __init__(self):
        self.tasks: dict[int, asyncio.Task] = {}

    async def device_alarm_worker(self, device: Device):
        """
        Worker for a single device listener.
        """
        while True:
            try:
                headers = build_hik_auth(device)
                async for alarm in get_alarm(device, headers):
                    message = build_alarm_message(alarm)

                    await send_alarm_to_n8n_webhook(
                        user_id=device.owner_superadmin_id,
                        device_id=device.id,
                        message=message,
                    )
                    await save_alarm_message_async(
                        user_id=device.owner_superadmin_id,
                        alarm= alarm,
                        device_id=device.id,
                        message=message,
                    )
            except asyncio.CancelledError:
                logger.info(f"[ALARM][{device.id}] Worker task cancelled")
                break
            except Exception as ex:
                logger.error(f"[ALARM][{device.id}] error: {ex}")
                await asyncio.sleep(5)  # backoff before retry

    async def fetch_valid_devices(self):
        """
        Fetch devices that are checked and belong to active users.
        """
        async with AsyncSessionLocal() as session:
            stmt = (
                select(Device)
                .join(User, Device.owner_superadmin_id == User.id)
                .where(
                    Device.is_checked == True,
                    User.is_active == True,
                )
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    async def sync_tasks(self):
        """
        Synchronize tasks with current list of valid devices.
        Starts new workers and stops removed ones.
        """
        devices = await self.fetch_valid_devices()
        valid_ids = {d.id for d in devices}

        # Start new tasks
        for d in devices:
            if d.id not in self.tasks:
                logger.info(f"[SUPERVISOR] Starting worker for device {d.id}")
                task = asyncio.create_task(self.device_alarm_worker(d))
                self.tasks[d.id] = task

        # Stop removed tasks
        for device_id in list(self.tasks.keys()):
            if device_id not in valid_ids:
                logger.info(f"[SUPERVISOR] Stopping worker for device {device_id}")
                self.tasks[device_id].cancel()
                del self.tasks[device_id]

    async def run(self):
        """
        Main loop for the supervisor.
        """
        while True:
            try:
                await self.sync_tasks()
            except Exception as ex:
                logger.error(f"[SUPERVISOR] Error syncing tasks: {ex}")

            await asyncio.sleep(10)  # sync interval

