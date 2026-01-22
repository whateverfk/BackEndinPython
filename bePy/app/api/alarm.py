from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select, delete
from datetime import datetime

from app.db.session import get_async_db as get_db
from app.Models.device import Device
from app.api.deps import CurrentUser, get_current_user
from app.Models.AlarmMessege import AlarmMessage
from app.schemas.alarmMessSche import AlarmPage
from app.core.constants import ERROR_MSG_ALARM_NOT_FOUND

router = APIRouter(
    prefix="/api/user/alarm",
    tags=["Alarm"]
)

PAGE_SIZE = 25


# =========================
# GET ALARMS (CURSOR PAGINATION)
# =========================
@router.get("")
@router.get("")
async def get_alarm_messages(
    cursor_time: datetime | None = None,
    cursor_id: int | None = None,
   
    device_id: int | None = Query(None),
    event: str | None = Query(None),
    channel_id_in_device: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    query = (
        select(
            AlarmMessage.id,
            AlarmMessage.device_id,
            AlarmMessage.event,
            AlarmMessage.channel_id_in_device,
            AlarmMessage.channel_name,
            AlarmMessage.message,
            AlarmMessage.created_at,
            Device.ip_web,  # Thêm ip_web từ Device
        )
        .outerjoin(Device, AlarmMessage.device_id == Device.id)  # Join với Device
        .where(AlarmMessage.user_id == user.superadmin_id)
    )
    # =========================
    # FILTERS
    # =========================
    if device_id is not None:
        query = query.where(AlarmMessage.device_id == device_id)
    if event is not None:
        query = query.where(AlarmMessage.event == event)
    if channel_id_in_device is not None:
        query = query.where(
            AlarmMessage.channel_id_in_device == channel_id_in_device
        )
    # =========================
    # CURSOR PAGINATION
    # =========================
    query = query.order_by(
        AlarmMessage.created_at.desc(),
        AlarmMessage.id.desc(),
    )
    if cursor_time and cursor_id:
        query = query.where(
            or_(
                AlarmMessage.created_at < cursor_time,
                and_(
                    AlarmMessage.created_at == cursor_time,
                    AlarmMessage.id < cursor_id,
                ),
            )
        )
    result = await db.execute(query.limit(PAGE_SIZE + 1))
    rows = result.all()
    has_more = len(rows) > PAGE_SIZE
    items = rows[:PAGE_SIZE]
    next_cursor_time = None
    next_cursor_id = None
    if items:
        last = items[-1]
        next_cursor_time = last.created_at
        next_cursor_id = last.id
    return {
        "items": [
            {
                "id": r.id,
                "device_id": r.device_id,
                "device_ip_web": r.ip_web,  # Thêm ip_web vào response
                "event": r.event,
                "channel_id_in_device": r.channel_id_in_device,
                "channel_name": r.channel_name,
                "message": r.message,
                "created_at": r.created_at,
            }
            for r in items
        ],
        "next_cursor_time": next_cursor_time,
        "next_cursor_id": next_cursor_id,
        "has_more": has_more,
    }
    
# =========================
# DELETE ONE ALARM
# =========================
@router.delete("/{alarm_id}")
@router.delete("/{alarm_id}")
async def delete_alarm_message(
    alarm_id: int,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    result = await db.execute(
        select(AlarmMessage)
        .where(
            AlarmMessage.id == alarm_id,
            AlarmMessage.user_id == user.superadmin_id
        )
    )
    alarm = result.scalars().first()

    if not alarm:
        raise HTTPException(status_code=404, detail=ERROR_MSG_ALARM_NOT_FOUND)

    await db.delete(alarm)
    await db.commit()

    return {"detail": "Alarm deleted successfully"}


# =========================
# DELETE ALL ALARMS
# =========================
@router.delete("")
@router.delete("")
async def delete_all_alarm_messages(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    # For sync session, default delete() returns count.
    # For async session, we execute delete() statement.
    # To get count, we might need a separate count query or check rowcount if supported (DBAPI dependent).
    # Since existing logic returns count, we should try to preserve it.
    
    # Simple approach: delete. rowcount might be available in result.
    stmt = delete(AlarmMessage).where(AlarmMessage.user_id == user.superadmin_id)
    result = await db.execute(stmt)
    deleted_count = result.rowcount if hasattr(result, 'rowcount') else 0

    await db.commit()

    return {
        "detail": "All alarms deleted",
        "deleted_count": deleted_count
    }
