from sqlalchemy import select
from app.Models.device_system_info import DeviceSystemInfo
from app.db.session import get_db
from app.features.GetDevicesDetail.HikDetailService import HikDetailService
from app.Models.channel_extensions import ChannelExtension
from app.Models.channel_stream_config import ChannelStreamConfig
from sqlalchemy.orm import Session

async def saveSystemInfo(db, system_info: dict):
    stmt = select(DeviceSystemInfo).where(
        DeviceSystemInfo.device_id == system_info["device_id"]
    )
    result =  db.execute(stmt)
    obj = result.scalar_one_or_none()

    if obj:
        # update
        obj.model = system_info["model"]
        obj.serial_number = system_info["serial_number"]
        obj.firmware_version = system_info["firmware_version"]
        obj.mac_address = system_info["mac_address"]
    else:
        # insert
        obj = DeviceSystemInfo(**system_info)
        db.add(obj)

    await db.commit()


async def sync_channel_config(
    db: Session,
    device,
    channel,
    headers,
):
    hikservice = HikDetailService()
    # =========================
    # STREAM CONFIG
    # =========================
    stream_data = await hikservice.fetch_stream_config(device, channel, headers)
    if stream_data:
        if channel.stream_config:
            cfg = channel.stream_config
        else:
            cfg = ChannelStreamConfig(channel_id=channel.id)
            db.add(cfg)

        cfg.resolution_width = stream_data["resolution_width"]
        cfg.resolution_height = stream_data["resolution_height"]
        cfg.video_codec = stream_data["video_codec"]
        cfg.max_frame_rate = stream_data["max_frame_rate"]
        cfg.fixed_quality = stream_data["fixed_quality"]
        cfg.vbr_average_cap = stream_data["vbr_average_cap"]

    # =========================
    # MOTION DETECTION
    # =========================
    motion_enabled = await hikservice.fetch_motion_detection(device, channel, headers)

    if channel.extension:
        ext = channel.extension
    else:
        ext = ChannelExtension(channel_id=channel.id)
        db.add(ext)

    ext.motion_detect_enabled = motion_enabled

    db.flush()
