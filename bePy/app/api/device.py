from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, CurrentUser
from app.Models.device import Device
from app.Models.channel import Channel
from app.Models.channel_record_time_range import ChannelRecordTimeRange
from app.schemas.device import (
    DeviceCreate,
    DeviceUpdate,
    DeviceOut,
)
from app.schemas.channel_record import ChannelRecordDayOut
from app.core.time_provider import TimeProvider
from app.features.RecordInfo.deps import build_hik_auth
from app.features.RecordInfo.hikrecord import HikRecordService
from app.Models.channel_record_day import ChannelRecordDay

router = APIRouter(
    prefix="/api/devices",
    tags=["Devices"]
)

# =========================
# GET: /api/devices
# =========================
@router.get("", response_model=list[DeviceOut])
def get_devices(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    return db.query(Device).filter(
        Device.owner_superadmin_id == user.superadmin_id
    ).all()


# =========================
# POST: /api/devices
# =========================
@router.post("", response_model=DeviceOut, status_code=status.HTTP_201_CREATED)
def create_device(
    dto: DeviceCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    exists = db.query(Device).filter(
        Device.ip_web == dto.ip_web,
        Device.owner_superadmin_id == user.superadmin_id
    ).first()
    print("DTO RECEIVED:", dto.model_dump())

    if exists:
        raise HTTPException(status_code=409, detail="Device already exists")

    device = Device(
        ip_web=dto.ip_web,
        ip_nvr=dto.ip_nvr,
        username=dto.username,
        password=dto.password,
        brand=dto.brand,
        is_checked=dto.is_checked,
        owner_superadmin_id=user.superadmin_id
    )

    db.add(device)
    db.commit()
    db.refresh(device)
    return device


# =========================
# PUT: /api/devices/{id}
# =========================
@router.put("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def update_device(
    id: int,
    dto: DeviceUpdate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    device = db.query(Device).filter(
        Device.id == id,
        Device.owner_superadmin_id == user.superadmin_id
    ).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device.ip_web = dto.ip_web
    device.ip_nvr = dto.ip_nvr
    device.username = dto.username
    device.password = dto.password
    device.brand = dto.brand
    device.is_checked = dto.is_checked

    db.commit()
    return


# =========================
# DELETE: /api/devices/{id}
# =========================
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(
    id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    device = db.query(Device).filter(
        Device.id == id,
        Device.owner_superadmin_id == user.superadmin_id
    ).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    db.delete(device)
    db.commit()
    return

@router.get("/{id}", response_model=DeviceOut)
def get_device(
    id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    device = db.query(Device).filter(
        Device.id == id,
        Device.owner_superadmin_id == user.superadmin_id
    ).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    return device

@router.get("/{id}/channels")
def get_device_channels(
    id: int,
    db: Session = Depends(get_db)
):
    
    return db.query(Channel).filter(
        Channel.device_id == id
    ).all()

@router.get(
    "/channels/{channel_id}/record_days_full",
    response_model=list[ChannelRecordDayOut]
)
def get_channel_record_days_full(
    channel_id: int,
    db: Session = Depends(get_db)
):
    days = (
        db.query(ChannelRecordDay)
        .filter(ChannelRecordDay.channel_id == channel_id)
        .order_by(ChannelRecordDay.record_date.desc())
        .all()
    )

    return days

@router.post("/{id}/get_channels_record_info")
async def update_channels_record_info(
    id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    device = db.query(Device).filter(
        Device.id == id,
        Device.owner_superadmin_id == user.superadmin_id
    ).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # 
    headers = build_hik_auth(device)

    hik_service = HikRecordService()
    time = TimeProvider()
    now = time.now().date()

    try:
        
        # 1. XÓA CŨ
        db.query(Channel).filter(
            Channel.device_id == device.id
        ).delete(synchronize_session=False)

        # 2. GET CHANNELS
        channels_data = await hik_service._get_channels(device, headers)
        if not channels_data:
            raise Exception("No channels returned from device")

        for ch in channels_data:
            print(f"[SYNC] Channel {ch}")

            oldest_date = await hik_service.oldest_record_date(
                device, ch["id"], headers
            )

            channel = Channel(
                device_id=device.id,
                channel_no=ch["id"],
                name=ch["name"],
                oldest_record_date=oldest_date,
                latest_record_date=now.strftime("%Y-%m-%d")
            )
            db.add(channel)
            db.flush()  # lấy channel.id
            print("add channel ok")
            record_days = await hik_service.record_status_of_channel(
                device,
                ch["id"],
                oldest_date,
                now.strftime("%Y-%m-%d"),
                headers
            )
            print(f"  Found {len(record_days)} record days.")
            for rd in record_days:
                record_day = ChannelRecordDay(
                    channel_id=channel.id,
                    record_date=rd["date"],
                    has_record=rd["has_record"]
                )
                db.add(record_day)
                print("  add record day ok")
                db.flush()

                if rd["has_record"]:
                    segments = await hik_service.get_time_ranges_segment(
                        device,
                        ch["id"],
                        rd["date"],
                        headers
                    )
                    segments = await hik_service.merge_time_ranges(
                        segments, gap_seconds=3
                    )
                    print(f"    Found {len(segments)} time range segments after merge.")

                    for seg in segments:
                        db.add(ChannelRecordTimeRange(
                            record_day_id=record_day.id,
                            start_time=seg.start_time,
                            end_time=seg.end_time
                        ))
                        print("    add time range ok")
        
        db.commit()

        return {"message": "Channels record info updated successfully"}

    except Exception as e:
        db.rollback()
        print("  ERROR:", e)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
