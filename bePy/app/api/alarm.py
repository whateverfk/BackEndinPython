from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime

from app.db.session import get_db
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
@router.get("", response_model=AlarmPage)
def get_alarm_messages(
    cursor_time: datetime | None = None,
    cursor_id: int | None = None,

   
    device_id: int | None = Query(None),
    event: str | None = Query(None),
    channel_id_in_device: str | None = Query(None),

    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    query = (
        db.query(
            AlarmMessage.id,
            AlarmMessage.device_id,
            AlarmMessage.event,
            AlarmMessage.channel_id_in_device,
            AlarmMessage.channel_name,
            AlarmMessage.message,
            AlarmMessage.created_at,
        )
        .filter(AlarmMessage.user_id == user.superadmin_id)
    )

    # =========================
    # FILTERS
    # =========================
    if device_id is not None:
        query = query.filter(AlarmMessage.device_id == device_id)

    if event is not None:
        query = query.filter(AlarmMessage.event == event)

    if channel_id_in_device is not None:
        query = query.filter(
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
        query = query.filter(
            or_(
                AlarmMessage.created_at < cursor_time,
                and_(
                    AlarmMessage.created_at == cursor_time,
                    AlarmMessage.id < cursor_id,
                ),
            )
        )

    rows = query.limit(PAGE_SIZE + 1).all()

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
def delete_alarm_message(
    alarm_id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    alarm = (
        db.query(AlarmMessage)
        .filter(
            AlarmMessage.id == alarm_id,
            AlarmMessage.user_id == user.superadmin_id
        )
        .first()
    )

    if not alarm:
        raise HTTPException(status_code=404, detail=ERROR_MSG_ALARM_NOT_FOUND)

    db.delete(alarm)
    db.commit()

    return {"detail": "Alarm deleted successfully"}


# =========================
# DELETE ALL ALARMS
# =========================
@router.delete("")
def delete_all_alarm_messages(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    deleted_count = (
        db.query(AlarmMessage)
        .filter(AlarmMessage.user_id == user.superadmin_id)
        .delete(synchronize_session=False)
    )

    db.commit()

    return {
        "detail": "All alarms deleted",
        "deleted_count": deleted_count
    }
