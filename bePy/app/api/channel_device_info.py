from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.Models.device import Device
from app.Models.channel import Channel
from app.api.deps import get_current_user, CurrentUser
from app.Models.device_system_info import DeviceSystemInfo
from app.features.GetDevicesDetail.HikDetailService import HikDetailService
from app.features.deps import build_hik_auth
from app.schemas.ChannelUpdate import ChannelUpdateSchema
from app.Models.channel_extensions import ChannelExtension
from app.Models.channel_stream_config import ChannelStreamConfig
from app.features.GetDevicesDetail.WorkWithDb import sync_channel_config
from app.features.Schedule_Racord_Mode.work_with_db import get_channel_recording_mode_from_db, sync_channel_recording_mode
import logging
router = APIRouter(
    prefix="/api/device/{device_id}/channel/{channel_id}/infor",
    tags=["Device_channel_info"]
)


@router.get("")
async def get_channel_info(
    device_id: int,
    channel_id: int,
    db: Session = Depends(get_db),
):
    channel = (
        db.query(Channel)
        .filter(
            Channel.id == channel_id,
            Channel.device_id == device_id
        )
        .first()
    )

    #  KHÔNG TỒN TẠI → 404 NGAY
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    #  CÓ CHANNEL NHƯNG CHƯA CÓ CONFIG → AUTO SYNC
    if not channel.stream_config or not channel.extension:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(404, "Device not found")

        headers = build_hik_auth(device)

        await sync_channel_config(
            db=db,
            device=device,
            channel=channel,
            headers=headers,
        )

        db.commit()
        db.refresh(channel)

    #  RETURN
    return {
        "id": channel.id,
        "channel_name": channel.name,
        "connected_type": channel.connected_type,

        "motion_detect": channel.extension.motion_detect_enabled
        if channel.extension else False,

        "resolution_width": channel.stream_config.resolution_width
        if channel.stream_config else None,

        "resolution_height": channel.stream_config.resolution_height
        if channel.stream_config else None,

        "video_codec": channel.stream_config.video_codec
        if channel.stream_config else None,

        "max_frame_rate": channel.stream_config.max_frame_rate
        if channel.stream_config else None,

        "fixed_quality": channel.stream_config.fixed_quality
        if channel.stream_config else None,

        "vbr_average_cap": channel.stream_config.vbr_average_cap
        if channel.stream_config else None,
        "vbr_upper_cap": channel.stream_config.vbr_upper_cap
        if channel.stream_config else None,
        "h265_plus": channel.stream_config.h265_plus
        if channel.stream_config else None,

    }

@router.put("")
async def update_channel_info(
    device_id: int,
    channel_id: int,
    data: ChannelUpdateSchema,
    db: Session = Depends(get_db),
):
    channel = (
        db.query(Channel)
        .filter(
            Channel.id == channel_id,
            Channel.device_id == device_id
        )
        .first()
    )

    if not channel:
        raise HTTPException(404, "Channel not found")

    # -------- BASIC INFO --------
    channel.name = data.channel_name

    # -------- MOTION --------
    if not channel.extension:
        channel.extension = ChannelExtension(channel_id=channel.id)

    channel.extension.motion_detect_enabled = data.motion_detect

    # -------- STREAM CONFIG --------
    if not channel.stream_config:
        channel.stream_config = ChannelStreamConfig(channel_id=channel.id)

    cfg = channel.stream_config
    cfg.resolution_width = data.resolution_width
    cfg.resolution_height = data.resolution_height
    cfg.video_codec = data.video_codec
    cfg.max_frame_rate = data.max_frame_rate
    cfg.fixed_quality = data.fixed_quality
    cfg.vbr_average_cap = data.vbr_average_cap
    cfg.h265_plus = data.h265_plus
    cfg.vbr_upper_cap = data.vbr_upper_cap

    #  Commit DB trước
    
    db.commit()
    db.refresh(channel)

    # -------- PUSH TO DEVICE --------
    device = (
    db.query(Device)
    .filter(Device.id == device_id)
    .first())

    if not device:
        raise HTTPException(404, "Device not found")


    headers = build_hik_auth(device)  # auth hik / proxy
    device_service = HikDetailService()
    try:

        await device_service.push_channel_config_to_device(
            device=device,
            channel=channel,
            headers=headers
        )
    except Exception as e:
        #  DB đã commit → chỉ cảnh báo
        raise HTTPException(
            status_code=502,
            detail=f"Saved but failed to push config to device: {str(e)}"
        )

    return {"status": "ok"}


@router.get("/capabilities")
async def get_channel_capabilities(
    device_id: int,
    channel_id: int,
    db: Session = Depends(get_db)
):
    channel = (
        db.query(Channel)
        .filter(
            Channel.id == channel_id,
            Channel.device_id == device_id
        )
        .first()
    )

    if not channel:
        raise HTTPException(404, "Channel not found")

    device = channel.device
    headers = build_hik_auth(device)
    hikservice = HikDetailService()

    return await hikservice.get_streaming_capabilities(
        device=device,
        channel=channel,
        headers=headers
    )



@router.get("/sync")
async def sync_channel_from_device(
    device_id: int,
    channel_id: int,
    db: Session = Depends(get_db)
):
    print("========== SYNC CHANNEL ==========")
    print(f"device_id={device_id}, channel_id={channel_id}")

    channel = (
        db.query(Channel)
        .filter(
            Channel.id == channel_id,
            Channel.device_id == device_id
        )
        .first()
    )

    if not channel:
        print(" Channel not found in DB")
        raise HTTPException(404, "Channel not found")

    device = channel.device
    headers = build_hik_auth(device)

    print(f"Device IP: {device.ip_web}")
    print(f"Channel No: {channel.channel_no}")
    print(f"Connected type: {channel.connected_type}")

    hikservice = HikDetailService()

    # =========================
    # 1. CHANNEL NAME
    # =========================
    print("▶ Sync channel name:", channel.name)

    # =========================
    # 2. MOTION DETECTION
    # =========================
    print("▶ Fetch motion detection ...")
    motion_enabled = await hikservice.fetch_motion_detection(
        device=device,
        channel=channel,
        headers=headers
    )
    print("✔ Motion detection enabled:", motion_enabled)

    if not channel.extension:
        print("➕ Create ChannelExtension")
        channel.extension = ChannelExtension(channel_id=channel.id)

    channel.extension.motion_detect_enabled = motion_enabled

    # =========================
    # 3. STREAM CONFIG
    # =========================
    print(" Fetch stream config ...")
    stream_data = await hikservice.fetch_stream_config(
        device=device,
        channel=channel,
        headers=headers
    )

    print(" Stream config raw data:")
    print(stream_data)

    if stream_data:
        if not channel.stream_config:
            print(" Create ChannelStreamConfig")
            channel.stream_config = ChannelStreamConfig(
                channel_id=channel.id
            )

        cfg = channel.stream_config

        cfg.resolution_width = stream_data.get("resolution_width")
        cfg.resolution_height = stream_data.get("resolution_height")
        cfg.video_codec = stream_data.get("video_codec")
        cfg.max_frame_rate = stream_data.get("max_frame_rate")
        cfg.fixed_quality = stream_data.get("fixed_quality")
        cfg.vbr_average_cap = stream_data.get("vbr_average_cap")
        cfg.vbr_upper_cap = stream_data.get("vbr_upper_cap")
        cfg.h265_plus = stream_data.get("h265_plus")

        print("✔ Stream config mapped to DB:")
        print({
            "resolution_width": cfg.resolution_width,
            "resolution_height": cfg.resolution_height,
            "video_codec": cfg.video_codec,
            "max_frame_rate": cfg.max_frame_rate,
            "fixed_quality": cfg.fixed_quality,
            "vbr_average_cap": cfg.vbr_average_cap,
            "vbr_upper_cap"  : cfg.vbr_upper_cap,
            "h265_plus" : cfg.h265_plus 
        })
    else:
        print("⚠ stream_data is EMPTY")

    print("▶ Commit DB ...")
    db.commit()
    print("✔ DB committed")

    # =========================
    # 4. RETURN FOR FRONTEND
    # =========================
    result = {
        "channel_name": channel.name,
        "connected_type": channel.connected_type,
        "motion_detect": channel.extension.motion_detect_enabled,

        "resolution_width": channel.stream_config.resolution_width if channel.stream_config else None,
        "resolution_height": channel.stream_config.resolution_height if channel.stream_config else None,
        "video_codec": channel.stream_config.video_codec if channel.stream_config else None,
        "max_frame_rate": channel.stream_config.max_frame_rate if channel.stream_config else None,
        "fixed_quality": channel.stream_config.fixed_quality if channel.stream_config else None,
        "vbr_average_cap": channel.stream_config.vbr_average_cap if channel.stream_config else None,
        "vbr_upper_cap":channel.stream_config.vbr_upper_cap if channel.stream_config else None,
        "h265_plus":channel.stream_config.h265_plus if channel.stream_config else None,

    }

    print("▶ Return to frontend:")
    print(result)
    print("========== SYNC DONE ==========")

    return result


@router.get("/recording-mode")
async def get_channel_recording_mode(
    device_id: int,
    channel_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    # ===============================
    # 1. Validate channel thuộc device
    # ===============================
    channel = db.query(Channel).filter(
        Channel.id == channel_id,
        Channel.device_id == device_id
    ).first()

    if not channel:
        raise HTTPException(
            status_code=404,
            detail="Channel not found for this device"
        )

    # ===============================
    # 2. Lấy recording mode từ DB
    # ===============================

    data = get_channel_recording_mode_from_db(
        db=db,
        channel_id=channel_id
    )

    if not data:
        return {
            "channel_id": channel_id,
            "default_mode": None,
            "timeline": []
        }

    # ==========
    return {
        "device_id": device_id,
        "channel_id": channel_id,
        "channel_no": channel.channel_no,
        "default_mode": data["default_mode"],
        "timeline": data["timeline"]
    }

@router.post("/recording-mode/sync")
async def sync_recording_mode(
    device_id: int,
    channel_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # ===============================
    # 1. Load device + channel
    # ===============================
    device = db.query(Device).filter(
        Device.id == device_id
    ).first()

    if not device:
        raise HTTPException(404, "Device not found")

    channel = db.query(Channel).filter(
        Channel.id == channel_id,
        Channel.device_id == device_id
    ).first()

    if not channel:
        raise HTTPException(404, "Channel not found")

    # ===============================
    # 2. Build ISAPI auth header
    # ===============================
    headers = build_hik_auth(device)

    # ===============================
    # 3. Sync from NVR → DB
    # ===============================
    data = await sync_channel_recording_mode(
        db=db,
        device=device,
        channel=channel,
        headers=headers
    )

    if not data:
        raise HTTPException(502, "Failed to sync from NVR")

    # ===============================
    # 4. Return latest DB data
    # ===============================
    return {
        "success": True,
        "data": get_channel_recording_mode_from_db(db, channel_id)
    }

