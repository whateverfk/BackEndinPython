from fastapi import APIRouter, Depends, HTTPException
from app.api.device import get_devices
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db, get_current_user, CurrentUser
from app.Models.device import Device
from app.schemas.channel_view import DeviceChannelView, ChannelView, TimeRangeView
from app.features.RecordInfo import hikrecord

router = APIRouter(prefix="/api/channels", tags=["Record"])
record_service = hikrecord.HikRecordService()


# =========================
# GET: 
# =========================

@router.get(
    "",
    response_model=List[DeviceChannelView]
)
async def get_device_channels(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    devices = (
        db.query(Device)
        .filter(Device.owner_superadmin_id == user.superadmin_id)
        .all()
    )

    result: List[DeviceChannelView] = []

    for device in devices:
        channels_info = await record_service.get_channels_record_info(device)

        result.append(
            DeviceChannelView(
                id=device.id,
                ip=device.ip_web,
                username=device.username,
                channels=[
                    ChannelView(
                        id=ch.channel_id,  # Sử dụng dot notation
                        name=ch.channel_name,  # Sử dụng dot notation
                        time_ranges=[
                            TimeRangeView(
                                start=tr.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                                end=tr.end_time.strftime("%Y-%m-%d %H:%M:%S")
                            )
                            for tr in ch.time_ranges  # Sử dụng dot notation
                        ]
                    )
                    for ch in channels_info
                ]
            )
        )

    return result
