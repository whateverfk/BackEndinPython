from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.Models.device import Device
from app.Models.channel import Channel
from app.api.deps import get_current_user, CurrentUser
from app.features.deps import build_hik_auth
from app.features.Schedule_Racord_Mode.work_with_db import sync_channel_recording_mode
from app.services.device_service import get_device_or_404, get_device_channels
from app.core.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(
    prefix="/api/device/{device_id}/channels",
    tags=["Device_channel_info"]
)


@router.post("/recording-mode/sync")
async def sync_recording_mode_all_channels(
    device_id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    """
    Sync recording mode for all channels of a device from ISAPI.
    """
    device = get_device_or_404(db, device_id)
    channels = get_device_channels(db, device_id)

    if not channels:
        raise HTTPException(404, "No channels found")

    headers = build_hik_auth(device)

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
            logger.error(f"Failed to sync recording mode for channel {ch.id}: {e}")
            failed.append({
                "channel_id": ch.id,
                "error": str(e)
            })

    return {
        "success": True,
        "synced_channels": success,
        "failed_channels": failed
    }

