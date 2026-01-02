import httpx
import uuid
import xml.etree.ElementTree as ET
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
from typing import List
from app.schemas.record import (
    ChannelRecordInfo,
    RecordTimeRange
)
from app.features.deps import build_hik_auth
from app.core.time_provider import TimeProvider
from sqlalchemy.orm import Session
from app.Models.device import Device    
from app.Models.channel import Channel
from app.Models.channel_record_day import ChannelRecordDay
from collections import defaultdict
from app.Models.channel_record_time_range import ChannelRecordTimeRange
from app.core.http_client import get_http_client

class HikRecordService():
    def __init__(self):
        self.client = get_http_client()

    async def _get_channels(self, device, headers):
        base_url = f"http://{device.ip_web}"
        endpoints = [
            ("/ISAPI/System/Video/inputs/channels", "VideoInputChannel", "local"),
            ("/ISAPI/ContentMgmt/InputProxy/channels", "InputProxyChannel", "proxy"),
        ]

        channels = []

        
        for endpoint, tag_name, ctype in endpoints:
                url = f"{base_url}{endpoint}"
                print(f"Requesting URL: {repr(url)}")

                try:
                    resp = await self.client.get(url, headers=headers, timeout=10)
                    resp.raise_for_status()

                    root = ET.fromstring(resp.text)
                    ns = {"hik": "http://www.hikvision.com/ver20/XMLSchema"}

                    for ch in root.findall(f".//hik:{tag_name}", ns):
                        cam_id = int(ch.find("hik:id", ns).text)
                        cam_name = ch.find("hik:name", ns).text

                        cam_id = cam_id * 100 + 1

                        channels.append({
                            "id": cam_id,
                            "name": cam_name,
                            "connected_type": ctype   # ⭐
                        })

                except Exception as ex:
                    print(f"Error fetching channels from {url}: {ex}")
                    return []

        return channels

    async def oldest_record_date(self, device, channel_id: int, headers) -> str | None:

            time_provider = TimeProvider()
            now = time_provider.now()
            year = now.year
            month = now.month
            base_url = f"http://{device.ip_web}"
            oldest_date: str | None = None
           
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

                    resp = await self.client.post(
                        url,
                        content=payload,
                        headers=headers
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
            print("ok Returning oldest record date:", oldest_date)
            return oldest_date

    async def get_time_ranges_segment(self, device, channel_id: int, date_str: str, headers) -> list[RecordTimeRange]:
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
            
           
            resp = await self.client.post(
                    f"{base_url}/ISAPI/ContentMgmt/search",
                    content=payload,
                    headers=headers
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

    async def record_status_of_channel(
        self,
        device,
        channel_id: int,
        start_date: str,
        end_date: str,
        header
    ) -> list[dict]:
        """
        Kiểm tra trạng thái record của channel trong khoảng ngày.
        
        """

        base_url = f"http://{device.ip_web}"
        url = f"{base_url}/ISAPI/ContentMgmt/record/tracks/{channel_id}/dailyDistribution"

        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        # Gom các ngày theo (year, month)
        months = defaultdict(list)
        current = start_dt
        while current <= end_dt:
            months[(current.year, current.month)].append(current)
            current += timedelta(days=1)

        results = []

        
        for (year, month), days_in_month in months.items():

                payload = f"""<?xml version="1.0" encoding="utf-8"?>
                <trackDailyParam>
                    <year>{year}</year>
                    <monthOfYear>{month}</monthOfYear>
                </trackDailyParam>
                """

                resp = await self.client.post(url, content=payload, headers=header)

                if resp.status_code != 200:
                    # Nếu lỗi → đánh false cho toàn bộ ngày trong tháng đó
                    for d in days_in_month:
                        results.append({
                            "date": d.strftime("%Y-%m-%d"),
                            "has_record": False
                        })
                    continue

                # Parse XML
                root = ET.fromstring(resp.text)

                # Map dayOfMonth -> has_record
                record_map = {}

                for day in root.findall(".//{*}day"):
                    day_num = int(day.find("{*}dayOfMonth").text)
                    record_text = day.find("{*}record")
                    record_map[day_num] = (
                        record_text is not None and record_text.text.lower() == "true"
                    )

                # Lấy đúng các ngày cần kiểm tra
                for d in days_in_month:
                    results.append({
                        "date": d.strftime("%Y-%m-%d"),
                        "has_record": record_map.get(d.day, False)
                    })

        return results

    async def sync_device_channels_data_core(
        self,
        db: Session,
        device: Device
    ):
            print(f"Start syncing device {device.id} channels data...")
            headers = build_hik_auth(device)
            hik_service = HikRecordService()
            time_provider = TimeProvider()
            today = time_provider.now().date()

            # =========================
            # 1. SYNC CHANNEL LIST
            # =========================
            nvr_channels = await hik_service._get_channels(device, headers)
            if not nvr_channels:
                return

            db_channels = db.query(Channel).filter(
                Channel.device_id == device.id
            ).all()

            db_map = {c.channel_no: c for c in db_channels}
            nvr_ids = {c["id"] for c in nvr_channels}

            for ch in nvr_channels:
                if ch["id"] not in db_map:
                    channel = Channel(
                        device_id=device.id,
                        channel_no=ch["id"],
                        connected_type=ch["connected_type"],
                        name=ch["name"],
                        is_active=True
                    )
                    db.add(channel)
                    db.flush()
                else:
                    channel = db_map[ch["id"]]
                    channel.name = ch["name"]
                    channel.connected_type = ch["connected_type"]
                    channel.is_active = True

                channel.last_channel_sync_at = datetime.utcnow()

            for ch_no, ch in db_map.items():
                if ch_no not in nvr_ids:
                    ch.is_active = False

            db.flush()

            # =========================
            # 2. SYNC RECORD DATA
            # =========================

            
            active_channels = db.query(Channel).filter(
                Channel.device_id == device.id,
                Channel.is_active == True
            ).all()

            for channel in active_channels:
                if channel.last_sync_at:
                    sync_from = channel.last_sync_at.date()
                else:
                    sync_from = channel.oldest_record_date or today

                print("Syncing channel", channel.channel_no, "from", sync_from)

                #  (1) LOAD TRƯỚC record_day CỦA CHANNEL
                existing_days = {
                    d.record_date: d
                    for d in db.query(ChannelRecordDay)
                    .filter(ChannelRecordDay.channel_id == channel.id)
                    .all()
                }

                #  (2) LẤY STATUS RECORD
                record_days = await hik_service.record_status_of_channel(
                    device,
                    channel.channel_no,
                    sync_from.strftime("%Y-%m-%d"),
                    today.strftime("%Y-%m-%d"),
                    headers
                )

                
                for rd in record_days:
                    record_date = datetime.strptime(rd["date"], "%Y-%m-%d").date()
                    has_record = rd["has_record"]

                    record_day = existing_days.get(record_date)

                    if not record_day:
                        record_day = ChannelRecordDay(
                            channel_id=channel.id,
                            record_date=record_date,
                            has_record=has_record
                        )
                        db.add(record_day)
                        db.flush()
                        existing_days[record_date] = record_day
                    else:
                        record_day.has_record = has_record

                    #  CHỈ SYNC SEGMENT GẦN HIỆN TẠI
                    if has_record and record_date >= today - timedelta(days=2):
                        segments = await hik_service.get_time_ranges_segment(
                            device,
                            channel.channel_no,
                            record_date.strftime("%Y-%m-%d"),
                            headers
                        )
                        segments = await hik_service.merge_time_ranges(segments)

                        db.query(ChannelRecordTimeRange).filter(
                            ChannelRecordTimeRange.record_day_id == record_day.id
                        ).delete(synchronize_session=False)

                        for seg in segments:
                            db.add(ChannelRecordTimeRange(
                                record_day_id=record_day.id,
                                start_time=seg.start_time,
                                end_time=seg.end_time
                            ))

                channel.last_sync_at = datetime.utcnow()
                channel.latest_record_date = today


    async def device_channels_init_data(
        self,
        db: Session,
        device: Device
    ):
        headers = build_hik_auth(device)
        hik_service = HikRecordService()
        today = TimeProvider().now().date()

        # KHÔNG begin / commit ở đây
        print("Inside init data")
        channels_data = await hik_service._get_channels(device, headers)
        if not channels_data:
            raise Exception("No channels returned from device")

        db.query(Channel).filter(
            Channel.device_id == device.id
        ).delete(synchronize_session=False)


        # =========================
# BATCH CHANNEL
# =========================

        channels_to_add = []
        channel_map = {}  # channel_no -> Channel instance

        for ch in channels_data:
            channel = Channel(
                device_id=device.id,
                channel_no=ch["id"],
                name=ch["name"],
                connected_type=ch["connected_type"],
                oldest_record_date=None,   # set sau
                latest_record_date=today
            )
            channels_to_add.append(channel)
            channel_map[ch["id"]] = channel

        db.add_all(channels_to_add)
        db.flush()  #  cần channel.id

        # =========================
        # BATCH RECORD DAY + TIME RANGE
        # =========================

        all_record_days = []
        all_time_ranges = []

        for ch in channels_data:
            channel = channel_map[ch["id"]]

            # ---- gọi API ----
            oldest_date = await hik_service.oldest_record_date(
                device, ch["id"], headers
            )
            channel.oldest_record_date = oldest_date

            record_days = await hik_service.record_status_of_channel(
                device,
                ch["id"],
                start_date=oldest_date,
                end_date=today.strftime("%Y-%m-%d"),
                header=headers
            )

            record_day_map = {}

            # ---- BATCH RECORD DAY ----
            for rd in record_days:
                rd_obj = ChannelRecordDay(
                    channel_id=channel.id,
                    record_date=rd["date"],
                    has_record=rd["has_record"]
                )
                all_record_days.append(rd_obj)
                record_day_map[rd["date"]] = rd_obj

            # ---- TIME RANGE (CHƯA ADD DB) ----
            for rd in record_days:
                if not rd["has_record"]:
                    continue

                segments = await hik_service.get_time_ranges_segment(
                    device,
                    ch["id"],
                    rd["date"],
                    headers
                )
                segments = await hik_service.merge_time_ranges(segments)

                record_day = record_day_map[rd["date"]]

                for seg in segments:
                    all_time_ranges.append(
                        ChannelRecordTimeRange(
                            record_day=record_day,  #  ORM relationship, chưa cần id
                            start_time=seg.start_time,
                            end_time=seg.end_time
                        )
                    )

        # =========================
        # COMMIT DB
        # =========================

        db.add_all(all_record_days)
        db.flush()  #  sinh record_day.id

        db.add_all(all_time_ranges)
        db.flush()

        print(
            f"Batch done: {len(channels_to_add)} channels | "
            f"{len(all_record_days)} record days | "
            f"{len(all_time_ranges)} time ranges"
        )

