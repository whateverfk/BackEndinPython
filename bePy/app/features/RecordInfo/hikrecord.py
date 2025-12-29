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
from app.features.RecordInfo.deps import build_hik_auth
from app.core.time_provider import TimeProvider
from sqlalchemy.orm import Session
from app.Models.device import Device    
from app.Models.channel import Channel
from app.Models.channel_record_day import ChannelRecordDay
from app.Models.channel_record_time_range import ChannelRecordTimeRange


class HikRecordService():

    async def _get_channels(self, device, headers):
        base_url = f"http://{device.ip_web}"
        endpoints = [
            ("/ISAPI/System/Video/inputs/channels", "VideoInputChannel", "local"),
            ("/ISAPI/ContentMgmt/InputProxy/channels", "InputProxyChannel", "proxy"),
        ]

        channels = []

        async with httpx.AsyncClient() as client:
            for endpoint, tag_name, ctype in endpoints:
                url = f"{base_url}{endpoint}"
                print(f"Requesting URL: {repr(url)}")

                try:
                    resp = await client.get(url, headers=headers, timeout=10)
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
            
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.post(
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

    async def record_status_of_channel(self, device, channel_id: int, start_date: str, end_date: str, header) -> list[dict]:

            """
            Kiểm tra xem trong khoảng thời gian từ `start_date` đến `end_date` có bản ghi nào hay không.
            
            """
            time_provider = TimeProvider()
            base_url = f"http://{device.ip_web}"
            
            # Convert start_date và end_date thành datetime để dễ thao tác
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d")

            record_status_list = []
            
            async with httpx.AsyncClient(timeout=15) as client:
                # Duyệt qua từng ngày từ start_date đến end_date
                current_date = start_datetime
                while current_date <= end_datetime:
                    payload = f"""<?xml version="1.0" encoding="utf-8"?>
                    <trackDailyParam>
                        <year>{current_date.year}</year>
                        <monthOfYear>{current_date.month}</monthOfYear>
                    </trackDailyParam>
                    """
                    
                    url = f"{base_url}/ISAPI/ContentMgmt/record/tracks/{channel_id}/dailyDistribution"
                    print(f"Requesting URL: {repr(url)}")

                    resp = await client.post(
                        url,
                        content=payload,
                        headers=header
                    )
                    
                    print(f"Response Status Code: {resp.status_code}")
                    
                    if resp.status_code != 200:
                        print("Error: API returned non-200 status.")
                        # Thêm thông tin lỗi vào danh sách trả về
                        record_status_list.append({"date": current_date.strftime("%Y-%m-%d"), "has_record": False})
                        current_date += timedelta(days=1)
                        continue
                    
                    root = ET.fromstring(resp.text)
                    days = root.findall(".//{*}day")

                    had_record = False
                    
                    for d in days:
                        record = d.find("{*}record")
                        if record is not None and record.text.lower() == "true":
                            had_record = True
                            break
                    
                    # Lưu trạng thái của ngày hiện tại vào danh sách
                    record_status_list.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "has_record": had_record
                    })
                    print(f"từ service gốc : Date: {current_date.strftime('%Y-%m-%d')}, Has Record: {had_record}")
                    
                    current_date += timedelta(days=1)
            print(f"Returning record status list with {len(record_status_list)} entries.")
            return record_status_list
        
    async def recorded_day_in_month(self, device, channel_id: int, year: int, month: int, header) -> list[dict]:



            time_provider = TimeProvider()
            base_url = f"http://{device.ip_web}"
            month = str(month)
            year = str(year)

            record_status_list = []
            

            async with httpx.AsyncClient(timeout=15) as client:
                payload = f"""<?xml version="1.0" encoding="utf-8"?>
                <trackDailyParam>
                    <year>{year}</year>
                    <monthOfYear>{month}</monthOfYear>
                </trackDailyParam>
                """
                
                url = f"{base_url}/ISAPI/ContentMgmt/record/tracks/{channel_id}/dailyDistribution"
                print(f"Requesting URL: {repr(url)}")

                resp = await client.post(
                    url,
                    content=payload,
                    headers=header
                )

                print(f"Response Status Code: {resp.status_code}")
                
                if resp.status_code != 200:
                    print("Error: API returned non-200 status.")
                    return []
                
                root = ET.fromstring(resp.text)
                
                # Tìm tất cả các thẻ <day> trong XML (xử lý namespace)
                days = root.findall(".//{http://www.hikvision.com/ver20/XMLSchema}day")

                for d in days:
                    day_of_month = int(d.find("{http://www.hikvision.com/ver20/XMLSchema}dayOfMonth").text)
                    record = d.find("{http://www.hikvision.com/ver20/XMLSchema}record")
                    has_record = (record is not None and record.text.lower() == "true")
                    
                    # Lưu trạng thái vào danh sách
                    record_status_list.append({
                        "date": f"{year}-{int(month):02d}-{day_of_month:02d}",
                        "has_record": has_record
                    })
                    
            print(f"Returning record status list with {len(record_status_list)} entries.")
            return record_status_list

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

                # bỏ comment để chỉ lấy dữ liệu 2 ngày gần nhất
                #sync_from = max(sync_from, today - timedelta(days=2))
                print("Syncing channel", channel.channel_no, "from", sync_from)
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

                    

                    record_day = db.query(ChannelRecordDay).filter(
                        ChannelRecordDay.channel_id == channel.id,
                        ChannelRecordDay.record_date == record_date
                    ).first()
                    

                    if not record_day:
                        record_day = ChannelRecordDay(
                            channel_id=channel.id,
                            record_date=record_date,
                            has_record=has_record
                        )
                        db.add(record_day)
                        db.flush()
                    else:
                        record_day.has_record = has_record
                    if has_record and record_date >= today - timedelta(days=2):
                        segments = await hik_service.get_time_ranges_segment(
                            device,
                            channel.channel_no,
                            record_date.strftime("%Y-%m-%d"),
                            headers
                        )
                        segments = await hik_service.merge_time_ranges(
                            segments
                        )

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
        """
        Atomic init:
        - channels
        - record days
        - time ranges
        """

        headers = build_hik_auth(device)
        hik_service = HikRecordService()
        today = TimeProvider().now().date()

        try:
            #  TRANSACTION BẮT ĐẦU
            with db.begin():

                # =========================
                # 1. GET CHANNELS TỪ NVR (TRƯỚC) KO CÓ THÔI LUÔN
                # =========================
                channels_data = await hik_service._get_channels(device, headers)
                if not channels_data:
                    raise Exception("No channels returned from device")

                # =========================
                # 2. XÓA CHANNEL CŨ
                # =========================
                db.query(Channel).filter(
                    Channel.device_id == device.id
                ).delete(synchronize_session=False)

                # =========================
                # 3. INIT TỪNG CHANNEL
                # =========================
                for ch in channels_data:
                    oldest_date = await hik_service.oldest_record_date(
                        device, ch["id"], headers
                    )

                    channel = Channel(
                        device_id=device.id,
                        channel_no=ch["id"],
                        name=ch["name"],
                        connected_type=ch["connected_type"],
                        oldest_record_date=oldest_date,
                        latest_record_date=today
                    )
                    db.add(channel)
                    db.flush()  # lấy channel.id

                    record_days = await hik_service.record_status_of_channel(
                        device,
                        ch["id"],
                        start_date=oldest_date,
                        end_date=today.strftime("%Y-%m-%d"),
                        header=headers
                    )

                    for rd in record_days:
                        record_day = ChannelRecordDay(
                            channel_id=channel.id,
                            record_date=rd["date"],
                            has_record=rd["has_record"]
                        )
                        db.add(record_day)
                        db.flush()

                        if rd["has_record"]:
                            segments = await hik_service.get_time_ranges_segment(
                                device,
                                ch["id"],
                                rd["date"],
                                headers
                            )
                            segments = await hik_service.merge_time_ranges(segments)

                            for seg in segments:
                                db.add(
                                    ChannelRecordTimeRange(
                                        record_day_id=record_day.id,
                                        start_time=seg.start_time,
                                        end_time=seg.end_time
                                    )
                                )

            db.commit()

        except Exception as e:
            # rollback tự động khi out khỏi db.begin()
            raise
