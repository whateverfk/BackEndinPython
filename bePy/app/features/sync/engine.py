from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.Models.device import Device
from app.Models.sync_log import SyncLog
from app.features.resolver import StrategyResolver
from app.core.time_provider import TimeProvider
import asyncio
from ping3 import ping
import uuid





class SyncEngine:

    def __init__(self):
        self.time = TimeProvider()
        self.resolver = StrategyResolver()

    async def sync_by_superadmin(self, db: AsyncSession, superadmin_id):
        # Nếu superadmin_id là UUID object, chuyển sang string
        if isinstance(superadmin_id, uuid.UUID):
            superadmin_id = str(superadmin_id)

        result = await db.execute(
            select(Device)
            .where(
                Device.owner_superadmin_id == superadmin_id,
                Device.is_checked == True
            )
        )
        devices = result.scalars().all()

        for d in devices:
            await self._sync_one(db, d, superadmin_id)

        await db.commit()

    async def _sync_one(self, db: AsyncSession, device, superadmin_id):

        try:
            strategy = self.resolver.sync_resolve(device.brand)
            result = await strategy.sync(device, self.time.now())

            log = SyncLog(
                device_id=device.id,
                ip=device.ip_web,
                is_success=result.success,
                sync_time=self.time.now(),
                message=result.message,
                owner_superadmin_id=superadmin_id
            )

            db.add(log)
        except Exception as ex:
            db.add(SyncLog(
                device_id=device.id,
                ip=device.ip_web,
                is_success=False,
                sync_time=self.time.now(),
                message=str(ex),
                owner_superadmin_id=superadmin_id
            ))
