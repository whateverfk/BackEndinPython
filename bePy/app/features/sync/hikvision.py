import base64
import httpx
from datetime import datetime

from app.features.sync.base import SyncStrategy
from app.schemas.sync import SyncResult
from app.core.http_client import get_http_client
from app.features.deps import build_hik_auth

class HikvisionSync(SyncStrategy):
    def __init__(self):
        self.client = get_http_client()
    async def sync(self, device, server_time: datetime) -> SyncResult:
        time_now = server_time.strftime("%Y-%m-%dT%H:%M:%S")

        xml = f"""
<Time xmlns="http://www.hikvision.com/ver20/XMLSchema">
  <timeMode>manual</timeMode>
  <localTime>{time_now}+07:00</localTime>
  <timeZone>CST-7:00:00</timeZone>
</Time>
"""

        url = f"http://{device.ip_web}/ISAPI/System/time"

        

        headers = build_hik_auth(device=device)

        try:
            
            res = await self.client.put(url, content=xml, headers=headers)

            if res.is_success:
                return SyncResult(
                    success=True,
                    message=f"IP:{device.ip_web} - HIK time sync successful"
                )

            return SyncResult(
                success=False,
                message=f"IP:{device.ip_web} - HIK HTTP {res.status_code}"
            )

        except Exception as ex:
            return SyncResult(
                success=False,
                message=f"IP:{device.ip_web} - Hik error {ex}"
            )
