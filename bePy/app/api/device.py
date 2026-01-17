from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.api.deps import get_db, get_current_user, CurrentUser
from app.Models.device import Device
from app.Models.channel import Channel
from app.Models.channel_record_time_range import ChannelRecordTimeRange
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceOut
from app.schemas.test_connect import DeviceConnectionTest, DeviceConnectionTestResult
from app.schemas.channel_record import ChannelRecordDayOut
from app.core.time_provider import TimeProvider
from app.features.deps import build_hik_auth, check_hikvision_auth, check_ip_reachable
from app.features.RecordInfo.hikrecord import HikRecordService
from app.Models.channel_record_day import ChannelRecordDay
from app.features.background.trigger_init_record_data import trigger_device_init_data
from app.services.device_service import (
    get_device_or_404,
    get_all_devices,
    get_active_devices,
    device_exists
)
from app.core.constants import (
    ERROR_MSG_DEVICE_NOT_FOUND,
    ERROR_MSG_DEVICE_EXISTS,
    ERROR_MSG_CANNOT_REACH_DEVICE,
    ERROR_MSG_UNSUPPORTED_BRAND,
    ERROR_MSG_AUTH_FAILED,
    ERROR_MSG_INVALID_DATE_FORMAT
)
from app.core.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(
    prefix="/api/devices",
    tags=["Devices"]
)


@router.post(
    "/test-connection",
    response_model=DeviceConnectionTestResult
)
def test_device_connection(
    dto: DeviceConnectionTest,
    user: CurrentUser = Depends(get_current_user)
):
    # 1. Check IP
    ip_ok = check_ip_reachable(dto.ip_web)

    if not ip_ok:
        return {
            "ip_reachable": False,
            "auth_ok": False,
            "message": ERROR_MSG_CANNOT_REACH_DEVICE
        }

    # 2. Check auth theo brand
    auth_ok = False

    if dto.brand.lower() == "hikvision":
        auth_ok = check_hikvision_auth(
            dto.ip_web,
            dto.username,
            dto.password
        )
    else:
        return {
            "ip_reachable": True,
            "auth_ok": False,
            "message": ERROR_MSG_UNSUPPORTED_BRAND
        }

    return {
        "ip_reachable": True,
        "auth_ok": auth_ok,
        "message": "OK" if auth_ok else ERROR_MSG_AUTH_FAILED
    }


# =========================
# GET: /api/devices
# =========================
@router.get("", response_model=list[DeviceOut])
def get_devices(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    """Get all devices for current user"""
    return get_all_devices(db, user.superadmin_id)




# =========================
# GET: /api/ active devices
# =========================
@router.get("/active", response_model=list[DeviceOut])
def get_active_devices_endpoint(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    """Get active (checked) devices for current user"""
    return get_active_devices(db, user.superadmin_id)


# =========================
# POST: /api/devices
# =========================
@router.post("", response_model=DeviceOut, status_code=status.HTTP_201_CREATED)
def create_device(
    dto: DeviceCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    """Create a new device"""
    if device_exists(db, dto.ip_web, user.superadmin_id):
        raise HTTPException(status_code=409, detail=ERROR_MSG_DEVICE_EXISTS)

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
    
    # Trigger background initialization
    background_tasks.add_task(trigger_device_init_data, device.id)
    
    return device


# =========================
# PUT: /api/devices/{id}
# =========================
@router.put("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def update_device(
    id: int,
    dto: DeviceUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    """Update device configuration (partial update allowed)"""

    device = get_device_or_404(db, id, user.superadmin_id)

    # Chỉ lấy những field frontend gửi lên
    data = dto.model_dump(exclude_unset=True)

    # Nếu không có gì để update → OK luôn
    if not data:
        return

    # Check đổi IP web để init lại
    should_reinitialize = (
        "ip_web" in data and data["ip_web"] != device.ip_web
    )

    # Update từng field
    for field, value in data.items():
        setattr(device, field, value)

    db.commit()

    # init lại data nếu đổi ip
    if should_reinitialize:
        background_tasks.add_task(trigger_device_init_data, device.id)

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
    """Delete a device"""
    device = get_device_or_404(db, id, user.superadmin_id)
    
    db.delete(device)
    db.commit()
    return

@router.get("/{id}", response_model=DeviceOut)
def get_device(
    id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    """Get a single device by ID"""
    return get_device_or_404(db, id, user.superadmin_id)

@router.get("/{id}/channels")
def get_device_channels(
    id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
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
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
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
    device = get_device_or_404(db, id, user.superadmin_id)
    hikservice = HikRecordService()

    try:
        await hikservice.device_channels_init_data(
            db=db,
            device=device
        )
        return {"message": "Channels record info updated successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"[SYNC ERROR] Device {id}: {e}")
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
    """ trả về channel với record day - time range tại tháng tương ứng.
        date_str format: "YYYY-MM" (e.g., "2025-12")
          Response shape:
            [ { channel: {id,name,channel_no,oldest_record_date,latest_record_date},
              record_days: [ {record_date, has_record,
                time_ranges: [{start_time,end_time}, ...] } ] }, ... ] """
    device = get_device_or_404(db, id, user.superadmin_id)

    try:
        parsed_date = datetime.strptime(date_str, "%Y-%m")
        year, month = parsed_date.year, parsed_date.month
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=ERROR_MSG_INVALID_DATE_FORMAT
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
    device = get_device_or_404(db, id, user.superadmin_id)

    hikservice = HikRecordService()
    await hikservice.sync_device_channels_data_core(
        db=db,
        device=device
    )

    db.commit()

    return {"message": "Synced"}
