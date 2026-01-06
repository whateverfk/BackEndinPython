from sqlalchemy.orm import Session
from app.Models.device import Device
from app.Models.sync_log import SyncLog
from app.features.resolver import StrategyResolver
from app.core.time_provider import TimeProvider
import asyncio
from ping3 import ping
import uuid


async def ping_ip(ip: str, timeout: int = 2) -> bool:
    try:
        # ping() là sync → đưa vào thread
        delay = await asyncio.to_thread(
            ping,
            ip,
            timeout=timeout,
            unit="ms"
        )
        return delay is not None
    except Exception:
        return False



class SyncEngine:

    def __init__(self):
        self.time = TimeProvider()
        self.resolver = StrategyResolver()

    async def sync_by_superadmin(self, db: Session, superadmin_id):
        # Nếu superadmin_id là UUID object, chuyển sang string
        if isinstance(superadmin_id, uuid.UUID):
            superadmin_id = str(superadmin_id)

        devices = db.query(Device).filter(
            Device.owner_superadmin_id == superadmin_id,
            Device.is_checked == True
        ).all()

        for d in devices:
            await self._sync_one(db, d, superadmin_id)

        db.commit()

    async def _sync_one(self, db: Session, device, superadmin_id):
        ok = await ping_ip(device.ip_nvr)
        if not ok:
            db.add(SyncLog(
                device_id=device.id,
                ip=device.ip_nvr,
                is_success=False,
                sync_time=self.time.now(),
                message=f"IP:{device.ip_web} - Ping failed",
                owner_superadmin_id=superadmin_id
            ))
            print(f"IP:{device.ip_web} - Ping failed")
            return

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
