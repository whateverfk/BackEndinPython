from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.Models.AlarmMessege import AlarmMessage
from app.api.deps import CurrentUser, get_current_user
from app.Models.user import User
from fastapi import Query
from datetime import datetime
from sqlalchemy import and_, or_
from app.schemas.alarmMessSche import AlarmPage,AlarmItem

router = APIRouter(
    prefix="/api/user/alarm",
    tags=["Alarm"]
)





PAGE_SIZE = 25


@router.get("", response_model=AlarmPage)
def get_alarm_messages(
    cursor_time: datetime | None = None,
    cursor_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    query = (
        db.query(
            AlarmMessage.id,
            AlarmMessage.device_id,
            AlarmMessage.message,
            AlarmMessage.created_at,
        )
        .filter(AlarmMessage.user_id == current_user.superadmin_id)
        .order_by(
            AlarmMessage.created_at.desc(),
            AlarmMessage.id.desc(),
        )
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

    # lấy dư 1 record để biết có còn trang sau không
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
                "message": r.message,
                "created_at": r.created_at,
            }
            for r in items
        ],
        "next_cursor_time": next_cursor_time,
        "next_cursor_id": next_cursor_id,
        "has_more": has_more,
    }


@router.delete("/{alarm_id}")
def delete_alarm_message(
    alarm_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    alarm = (
        db.query(AlarmMessage)
        .filter(
            AlarmMessage.id == alarm_id,
            AlarmMessage.user_id == current_user.superadmin_id
        )
        .first()
    )

    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")

    db.delete(alarm)
    db.commit()

    return {"detail": "Alarm deleted successfully"}


@router.delete("")
def delete_all_alarm_messages(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    deleted = (
        db.query(AlarmMessage)
        .filter(AlarmMessage.user_id == current_user.superadmin_id)
        .delete(synchronize_session=False)
    )

    db.commit()

    return {
        "detail": "All alarms deleted",
        "deleted_count": deleted
    }
