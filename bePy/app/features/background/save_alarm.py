import asyncio
from sqlalchemy import select
from app.features.alarm_nofi.alarm import get_alarm,save_alarm_message_async,build_alarm_message
from app.Models.device import Device
from app.features.deps import build_hik_auth
from app.db.session import AsyncSessionLocal
from app.Models.user import User


class AlarmSupervisor:
    def __init__(self):
        self.tasks: dict[int, asyncio.Task] = {}

    async def device_alarm_worker(self, device:Device     ):
        """
        Worker cho 1 device duy nhất
        """
        headers = build_hik_auth(device)

        while True:
            try:
                async for alarm in get_alarm(device, headers):
                    message = build_alarm_message(
                        alarm,
                        device_name=device.ip_web,
                    )

                    await save_alarm_message_async(
                        user_id=device.owner_superadmin_id,
                        device_id=device.id,
                        message=message,
                    )

            except asyncio.CancelledError:
                # task bị supervisor cancel
                break

            except Exception as ex:
                # lỗi mạng, camera down...
                print(f"[ALARM][{device.id}] error: {ex}")
                await asyncio.sleep(5)  # backoff

    async def fetch_valid_devices(self):
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
        devices = await self.fetch_valid_devices()
        valid_ids = {d.id for d in devices}

        # start new tasks
        for d in devices:
            if d.id not in self.tasks:
                print(f"[SUPERVISOR] start device {d.id}")
                task = asyncio.create_task(self.device_alarm_worker(d))
                self.tasks[d.id] = task

        # stop removed tasks
        for device_id in list(self.tasks.keys()):
            if device_id not in valid_ids:
                print(f"[SUPERVISOR] stop device {device_id}")
                self.tasks[device_id].cancel()
                del self.tasks[device_id]

    async def run(self):
        while True:
            try:
                await self.sync_tasks()
            except Exception as ex:
                print("[SUPERVISOR] error:", ex)

            await asyncio.sleep(10)  # sync interval
