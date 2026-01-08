from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.Models.device import Device
from app.Models.channel import Channel
from app.api.deps import get_current_user
from app.features.deps import build_hik_auth
from app.features.Schedule_Racord_Mode.work_with_db import  sync_channel_recording_mode

router = APIRouter(
    prefix="/api/device/{device_id}/channels",
    tags=["Device_channel_info"]
)

@router.post("/recording-mode/sync")
async def sync_recording_mode_all_channels(
    device_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # ===============================
    # 1. Load device
    # ===============================
    device = db.query(Device).filter(
        Device.id == device_id
    ).first()

    if not device:
        raise HTTPException(404, "Device not found")

    # ===============================
    # 2. Load ALL channels
    # ===============================
    channels = db.query(Channel).filter(
        Channel.device_id == device_id
    ).all()

    if not channels:
        raise HTTPException(404, "No channels found")

    # ===============================
    # 3. Build ISAPI auth
    # ===============================
    headers = build_hik_auth(device)

    # ===============================
    # 4. Sync từng channel
    # ===============================
    success = []
    failed = []

    for ch in channels:
        try:
            await sync_channel_recording_mode(
                db=db,
                device=device,
                channel=ch,
                headers=headers
            )
            success.append(ch.id)
        except Exception as e:
            failed.append({
                "channel_id": ch.id,
                "error": str(e)
            })

    return {
        "success": True,
        "synced_channels": success,
        "failed_channels": failed
    }
