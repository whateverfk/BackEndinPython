from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.Models.channel_recording_mode import ChannelRecordingMode
from app.Models.channel_recoding_mode_time_line import ChannelRecordingModeTimeline
from app.features.Schedule_Racord_Mode.HikRecordingModeService import HikRecordingModeService
from datetime import time
from app.Models.recording_mode_enum_class import RecordingMode

DAY_MAP = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}
DAY_REVERSE_MAP = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday",
}

async def upsert_channel_recording_mode(
    db: AsyncSession,
    data: dict
):
    """
    data = {
        "channel_id": int,
        "default_mode": "CMR",
        "timeline": [
            {
                "day_start": "Sunday",
                "time_start": "06:02:00",

                "day_end": "Sunday",
                "time_end": "10:45:00",
                "mode": "MOTION"
            }
        ]
    }
    """

    channel_id = data["channel_id"]

    # ==================================
    # 1. UPSERT CHANNEL RECORDING MODE
    # ==================================
    result = await db.execute(
        select(ChannelRecordingMode)
        .where(ChannelRecordingMode.channel_id == channel_id)
    )
    mode_obj = result.scalars().first()

    if not mode_obj:
        mode_obj = ChannelRecordingMode(
            channel_id=channel_id,
            schedule_enabled=True
        )
        db.add(mode_obj)

    mode_obj.default_mode = RecordingMode(data["default_mode"])

    await db.flush()

    # ==================================
    # 2. RESET TIMELINE (BY CHANNEL)
    # ==================================
    await db.execute(
        delete(ChannelRecordingModeTimeline)
        .where(ChannelRecordingModeTimeline.channel_id == channel_id)
    )

    # ==================================
    # 3. INSERT TIMELINE
    # ==================================
    timelines = []

    for t in data.get("timeline", []):
        if not t.get("mode"):
            continue

        timelines.append(
            ChannelRecordingModeTimeline(
                channel_id=channel_id,
                day_of_week=DAY_MAP[t["day_start"]],
                start_time=time.fromisoformat(t["time_start"]),
                end_time=time.fromisoformat(t["time_end"]),
                day_end_of_week= DAY_MAP[t["day_end"]],
                mode=RecordingMode(t["mode"])
            )
        )

    if timelines:
        db.add_all(timelines)

    await db.commit()

async def sync_channel_recording_mode(
        db: AsyncSession,
        device,
        channel,
        headers
    ):
        service = HikRecordingModeService()

        data = await service.fetch_channel_recording_mode(
            device=device,
            channel=channel,
            headers=headers
        )

        if not data:
            return None

        await upsert_channel_recording_mode(db, data)

        return data

async def get_channel_recording_mode_from_db(
    db: AsyncSession,
    channel_id: int
):
    # ===============================
    # 1. LẤY DEFAULT MODE
    # ===============================
    result = await db.execute(
        select(ChannelRecordingMode)
        .where(ChannelRecordingMode.channel_id == channel_id)
    )
    mode = result.scalars().first()

    if not mode:
        return None

    # ===============================
    # 2. LẤY TIMELINE THEO CHANNEL
    # ===============================
    # ===============================
    # 2. LẤY TIMELINE THEO CHANNEL
    # ===============================
    result = await db.execute(
        select(ChannelRecordingModeTimeline)
        .where(ChannelRecordingModeTimeline.channel_id == channel_id)
        .order_by(
            ChannelRecordingModeTimeline.day_of_week,
            ChannelRecordingModeTimeline.start_time
        )
    )
    timelines = result.scalars().all()

    # ===============================
    # 3. MAP RA FORMAT FRONTEND
    # ===============================
    return {
        "channel_id": channel_id,
        "default_mode": mode.default_mode.value,   # Enum → string
        "schedule_enabled": mode.schedule_enabled,
        "timeline": [
            {
                "day_start": DAY_REVERSE_MAP[t.day_of_week],
                "time_start": t.start_time.strftime("%H:%M:%S"),
                "day_end": DAY_REVERSE_MAP[t.day_end_of_week],
                "time_end": t.end_time.strftime("%H:%M:%S"),
                "mode": t.mode.value
            }
            for t in timelines
        ]
    }