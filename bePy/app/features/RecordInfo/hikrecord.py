import httpx
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List
from app.schemas.record import (
    ChannelRecordInfo,
    RecordTimeRange
)
from app.features.RecordInfo.base import RecordService
from app.features.RecordInfo.deps import build_hik_auth
from app.core.time_provider import TimeProvider


class HikRecordService(RecordService):

    async def _get_channels(self, device, headers):
        base_url = f"http://{device.ip_web}"
        endpoints = [
            ("/ISAPI/System/Video/inputs/channels", "VideoInputChannel"),
            ("/ISAPI/ContentMgmt/InputProxy/channels", "InputProxyChannel")
        ]

        channels = []

        async with httpx.AsyncClient() as client:
            for endpoint, tag_name in endpoints:
                url = f"{base_url}{endpoint}"
                print(f"Requesting URL: {repr(url)}")
                try:
                    resp = await client.get(url, headers=headers, timeout=10)
                    resp.raise_for_status()

                    print(f"Response Status Code: {resp.status_code}")

                    root = ET.fromstring(resp.text)
                    ns = {"hik": "http://www.hikvision.com/ver20/XMLSchema"}

                    for ch in root.findall(f".//hik:{tag_name}", ns):
                        cam_id = int(ch.find("hik:id", ns).text)
                        cam_name = ch.find("hik:name", ns).text
                        cam_id = cam_id * 100 + 1
                        channels.append({"id": cam_id, "name": cam_name})
                except Exception as ex:
                    print(f"Error fetching channels from {url}: {ex}")
                    return []
                    

        print(f"Found {len(channels)} channels.")
        return channels

    async def oldest_record_date(self, device, channel_id: int) -> str | None:

        time_provider = TimeProvider()
        now = time_provider.now()
        year = now.year
        month = now.month
        base_url = f"http://{device.ip_web}"
        oldest_date: str | None = None
        async with httpx.AsyncClient(timeout=15) as client:
            while True:
                payload = f"""<?xml version="1.0" encoding="utf-8"?>
<trackDailyParam>
    <year>{year}</year>
    <monthOfYear>{month}</monthOfYear>
</trackDailyParam>
"""

                url = (
                    f"{base_url}"
                    f"/ISAPI/ContentMgmt/record/tracks/{channel_id}/dailyDistribution"
                )
                print(f"Requesting URL: {repr(url)}")

                resp = await client.post(
                    url,
                    content=payload,
                    headers=build_hik_auth(device)
                )

                print(f"Response Status Code: {resp.status_code}")

                if resp.status_code != 200:
                    print("Error: API returned non-200 status.")
                    break

                root = ET.fromstring(resp.text)
                days = root.findall(".//{*}day")

                record_days: list[int] = []

                for d in days:
                    record = d.find("{*}record")
                    if record is not None and record.text.lower() == "true":
                        day_num = int(d.find("{*}dayOfMonth").text)
                        record_days.append(day_num)

                # No records in this month
                if not record_days:
                    print(f"No records found for {year}-{month}. Moving to previous month.")
                    break

                # Found records, get the smallest (oldest) day
                oldest_day = min(record_days)
                oldest_date = f"{year}-{month:02d}-{oldest_day:02d}"
                print(f"Oldest record date: {oldest_date}")

                # Move to the previous month
                month -= 1
                if month == 0:
                    month = 12
                    year -= 1

        return oldest_date

    async def get_time_ranges_segment(self, device, channel_id: int, date_str: str) -> list[RecordTimeRange]:
        day = datetime.strptime(date_str, "%Y-%m-%d")
        day_start = datetime(day.year, day.month, day.day, 0, 0, 0)
        day_end = datetime(day.year, day.month, day.day, 23, 59, 59)

        # Expand the search by ±1 day to be sure
        search_start = day_start - timedelta(days=1)
        search_end = day_end + timedelta(days=1)

        # ========================
        # ISAPI SEARCH
        # ========================
        search_id = str(uuid.uuid4()).upper()
        base_url = f"http://{device.ip_web}"

        payload = f"""<?xml version="1.0" encoding="utf-8"?>
<CMSearchDescription>
  <searchID>{search_id}</searchID>
  <trackList>
    <trackID>{channel_id}</trackID>
  </trackList>
  <timeSpanList>
    <timeSpan>
      <startTime>{search_start.strftime('%Y-%m-%dT%H:%M:%S')}Z</startTime>
      <endTime>{search_end.strftime('%Y-%m-%dT%H:%M:%S')}Z</endTime>
    </timeSpan>
  </timeSpanList>
  <maxResults>200</maxResults>
  <searchResultPostion>0</searchResultPostion>
  <metadataList>
    <metadataDescriptor>//recordType.meta.std-cgi.com</metadataDescriptor>
  </metadataList>
</CMSearchDescription>
"""

        #print(f"Tìm từ ngày {search_start} tới {search_end}.")
        
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                f"{base_url}/ISAPI/ContentMgmt/search",
                content=payload,
                headers=build_hik_auth(device)
            )
          #  print(f"Requesting URL: {repr(f'{base_url}/ISAPI/ContentMgmt/search')}")
           # print(f"Response Status Code: {resp.status_code}")

        if resp.status_code != 200:
            #print("Error: API returned non-200 status.")
            return []

        # =========================
        # PARSE XML
        # ========================
        root = ET.fromstring(resp.text)
        items = root.findall(".//{*}searchMatchItem")

        result: list[RecordTimeRange] = []

        for item in items:
            ts = item.find("./{*}timeSpan")
            if ts is None:
                continue

            s = ts.find("{*}startTime")
            e = ts.find("{*}endTime")
            if s is None or e is None:
                continue

            start = datetime.fromisoformat(s.text.replace("Z", ""))
            end = datetime.fromisoformat(e.text.replace("Z", ""))
            
            # ====================
            # CLIP VÀ CHỈ GIỮ TRONG NGÀY
            # ====================
            if end <= day_start or start >= day_end:
                continue

            clipped_start = max(start, day_start)
            clipped_end = min(end, day_end)
            if clipped_start < clipped_end:
                result.append(
                    RecordTimeRange(
                        start_time=clipped_start,
                        end_time=clipped_end
                    )
                )

       # print(f"Tìm thấy {len(result)} record segment.")
       # print(f"Time ranges: {', '.join([f'{r.start_time.strftime('%Y-%m-%d %H:%M:%S')} → {r.end_time.strftime('%Y-%m-%d %H:%M:%S')}' for r in result])}")
        return result

    async def merge_time_ranges(self, ranges: List[RecordTimeRange], gap_seconds: int = 5) -> List[RecordTimeRange]:
        if not ranges:
            return []

        ranges = sorted(ranges, key=lambda r: r.start_time)
        merged: List[RecordTimeRange] = []
        tol = timedelta(seconds=gap_seconds)

        for r in ranges:
            if not merged:
                merged.append(r)
                continue

            last = merged[-1]
            if r.start_time <= last.end_time + tol:
                last.end_time = max(last.end_time, r.end_time)
            else:
                merged.append(r)
        
        #print(f"Merged {len(merged)} time ranges. ")
        #print(f"Time ranges after merge: {', '.join([f'{r.start_time.strftime('%Y-%m-%d %H:%M:%S')} → {r.end_time.strftime('%Y-%m-%d %H:%M:%S')} ' for r in merged])}")
    
        return merged

    async def get_channels_record_info(self, device) -> List[ChannelRecordInfo]:
        headers = build_hik_auth(device)

        channels = await self._get_channels(device, headers)

        result: List[ChannelRecordInfo] = []

        for ch in channels:
            oldest_date = await self.oldest_record_date(
                device,
                channel_id=ch["id"]
            )

            if oldest_date:
                time_ranges = await self.get_time_ranges_segment(
                    date_str=oldest_date,
                    device=device,
                    channel_id=ch["id"]
                )
                time_ranges = await self.merge_time_ranges(time_ranges)
            else:
                time_ranges = []

            result.append(
                ChannelRecordInfo(
                    channel_id=ch["id"],
                    channel_name=ch["name"],
                    oldest_date=oldest_date,
                    time_ranges=time_ranges
                )
            )

        print(f"Returning {len(result)} channel record info.")
        return result
