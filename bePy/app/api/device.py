from datetime import datetime, timedelta , date   
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
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
# GET: /api/devices
# =========================
@router.get("/active", response_model=list[DeviceOut])
def get_devices(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    return db.query(Device).filter(
        Device.owner_superadmin_id == user.superadmin_id,
        Device.is_checked == True
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


@router.get("/{id}/channels/records")
def get_device_channels_records(
    id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    """
    Return all channels for a device along with their record days and time ranges.
    Response shape: list of { channel: {id,name,channel_no,oldest_record_date,latest_record_date}, record_days: [ {record_date, has_record, time_ranges: [{start_time,end_time}, ...] } ] }
    """
    device = db.query(Device).filter(
        Device.id == id,
        Device.owner_superadmin_id == user.superadmin_id
    ).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # load channels
    channels = db.query(Channel).filter(Channel.device_id == device.id).all()

    result = []
    for ch in channels:
        # load record days and time ranges for each channel
        days = (
            db.query(ChannelRecordDay)
            .options(joinedload(ChannelRecordDay.time_ranges))
            .filter(ChannelRecordDay.channel_id == ch.id)
            .order_by(ChannelRecordDay.record_date.desc())
            .all()
        )

        # build serializable structure
        rd_list = []
        for rd in days:
            tr_list = []
            for tr in getattr(rd, 'time_ranges', []):
                tr_list.append({
                    'start_time': tr.start_time,
                    'end_time': tr.end_time
                })

            rd_list.append({
                'record_date': rd.record_date,
                'has_record': rd.has_record,
                'time_ranges': tr_list
            })

        result.append({
            'channel': {
                'id': ch.id,
                'channel_no': ch.channel_no,
                'name': ch.name,
                'oldest_record_date': ch.oldest_record_date,
                'latest_record_date': ch.latest_record_date
            },
            'record_days': rd_list
        })

    return result

@router.post("/{id}/get_channels_record_info")
async def update_channels_record_info(
    id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    
    """
    Cập nhật / tạo mới thông tin cho toàn bộ channels và các ngày có record + time ranges
      từng ngày của thiết bị.
    """
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
                start_date=oldest_date,
                end_date=now.strftime("%Y-%m-%d"),
                header=headers
            )
            print(f"  Found {len(record_days)} record days.")
            for rd in record_days:
                record_day = ChannelRecordDay(
                    channel_id=channel.id,
                    record_date=rd["date"],
                    has_record=rd["has_record"]
                )
                db.add(record_day)
                print(f"add record day ok {record_day.record_date}, bool {record_day.has_record} ")
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

@router.get("/{id}/channels/month_data/{date_str}")
def get_all_channels_data_in_month(
    id: int,
    date_str: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    """ Return all channels for a device along with their record days/time ranges limited to
      the specified month.
        date_str format: "YYYY-MM" (e.g., "2025-12")
          Response shape:
            [ { channel: {id,name,channel_no,oldest_record_date,latest_record_date},
              record_days: [ {record_date, has_record,
                time_ranges: [{start_time,end_time}, ...] } ] }, ... ] """
    device = db.query(Device).filter(
        Device.id == id,
        Device.owner_superadmin_id == user.superadmin_id
    ).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    try:
        parsed_date = datetime.strptime(date_str, "%Y-%m")
        year, month = parsed_date.year, parsed_date.month
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM"
        )

    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    channels = db.query(Channel).filter(
        Channel.device_id == device.id
    ).all()

    oldest_record_date_query = db.query(func.min(Channel.oldest_record_date).label('oldest_record_date')
    ).filter(
        Channel.device_id == device.id
    ).scalar()

    # Extract month and year from the oldest record date if available
    oldest_record_month = None
    if oldest_record_date_query:
        oldest_record_month = oldest_record_date_query.strftime("%Y-%m")


    result = []

    for ch in channels:
        days = (
            db.query(ChannelRecordDay)
            .options(joinedload(ChannelRecordDay.time_ranges))
            .filter(
                ChannelRecordDay.channel_id == ch.id,
                ChannelRecordDay.record_date >= first_day,
                ChannelRecordDay.record_date <= last_day
            )
            .order_by(ChannelRecordDay.record_date.desc())
            .all()
        )

        rd_list = []
        for rd in days:
            rd_list.append({
                "record_date": rd.record_date.isoformat(),
                "has_record": rd.has_record,
                "time_ranges": [
                    {
                        "start_time": tr.start_time.isoformat(),
                        "end_time": tr.end_time.isoformat()
                    }
                    for tr in rd.time_ranges
                ]
            })

        result.append({
            "channel": {
                "id": ch.id,
                "channel_no": ch.channel_no,
                "name": ch.name,
                "oldest_record_date": (
                    ch.oldest_record_date.isoformat()
                    if ch.oldest_record_date else None
                ),
                "latest_record_date": (
                    ch.latest_record_date.isoformat()
                    if ch.latest_record_date else None
                )
            },
            "record_days": rd_list
        })

    return {
        "oldest_record_month": oldest_record_month,
        "channels": result
    }
  
            
@router.post("/{id}/channelsdata/sync")
async def sync_device_channels_data(
    id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    device = db.query(Device).filter(
        Device.id == id,
        Device.owner_superadmin_id == user.superadmin_id
    ).first()

    if not device:
        raise HTTPException(status_code=404)

    hikservice = HikRecordService()
    await hikservice.sync_device_channels_data_core(
        db=db,
        device=device
    )

    db.commit()

    return {"message": "Synced"}
