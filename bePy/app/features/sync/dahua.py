import base64
import httpx
from datetime import datetime

from app.features.sync.base import SyncStrategy
from app.schemas.sync import SyncResult
from app.core.http_client import get_http_client
class DahuaSync(SyncStrategy):
    def __init__(self):
        self.client = get_http_client()
    

    async def sync(self, device, server_time: datetime) -> SyncResult:
        time_str = server_time.strftime("%Y-%m-%d %H:%M:%S")
        url = (
            f"http://{device.ip_web}/cgi-bin/global.cgi"
            f"?action=setCurrentTime&time={time_str}"
        )

        auth = base64.b64encode(
            f"{device.username}:{device.password}".encode()
        ).decode()

        headers = {"Authorization": f"Basic {auth}"}

        try:
            
            res = await self.client.get(url, headers=headers)

            if res.status_code != 200:
                return SyncResult(
                    success=False,
                    message=f"IP:{device.ip_web} - Dahua HTTP {res.status_code}"
                )

            if res.text.strip().upper() == "OK":
                return SyncResult(
                    success=True,
                    message=f"IP:{device.ip_web} - Dahua time sync successful"
                )

            return SyncResult(
                success=False,
                message=f"Dahua response: {res.text}"
            )

        except Exception as ex:
            return SyncResult(
                success=False,
                message=f"IP:{device.ip_web} - Dahua error: {ex}"
            )
