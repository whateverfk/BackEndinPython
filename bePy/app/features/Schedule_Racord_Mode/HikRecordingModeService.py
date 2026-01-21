import xml.etree.ElementTree as ET
from app.core.http_client import get_http_client



class HikRecordingModeService:
    def __init__(self):
        self.client = get_http_client()

    async def fetch_channel_recording_mode(
        self,
        device,
        channel,
        headers
    ):
        url = (
            f"http://{device.ip_web}"
            f"/ISAPI/ContentMgmt/record/tracks/{channel.channel_no}"
        )

        resp = await self.client.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        root = ET.fromstring(resp.text)
        ns = {"hik": "http://www.hikvision.com/ver20/XMLSchema"}

        default_mode = root.findtext(
            "hik:DefaultRecordingMode",
            namespaces=ns
        )

        timeline = []

        for act in root.findall(".//hik:ScheduleAction", namespaces=ns):
            mode = act.findtext(
                "hik:Actions/hik:ActionRecordingMode",
                namespaces=ns
            )

            if not mode:
                continue

            timeline.append({
                "day_start": act.findtext(
                    "hik:ScheduleActionStartTime/hik:DayOfWeek",
                    namespaces=ns
                ),
                "time_start": act.findtext(
                    "hik:ScheduleActionStartTime/hik:TimeOfDay",
                    namespaces=ns
                ),
                "day_end": act.findtext(
                    "hik:ScheduleActionEndTime/hik:DayOfWeek",
                    namespaces=ns
                ),
                "time_end": act.findtext(
                    "hik:ScheduleActionEndTime/hik:TimeOfDay",
                    namespaces=ns
                ),
                "mode": mode
            })
        result = {
            "channel_id": channel.id,
            "default_mode": default_mode,
            "timeline": timeline
        }

        

        return result

    
