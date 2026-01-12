from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.Models.AlarmMessege import AlarmMessage
from app.api.deps import CurrentUser, get_current_user
from app.Models.user import User


router = APIRouter(
    prefix="/api/user/alarm",
    tags=["Alarm"]
)


@router.get("", response_model=list[dict])
def get_alarm_messages(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    alarms = (
        db.query(AlarmMessage)
        .filter(AlarmMessage.user_id == current_user.superadmin_id)
        .order_by(AlarmMessage.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": alarm.id,
            "device_id": alarm.device_id,
            "message": alarm.message,
            "created_at": alarm.created_at,
        }
        for alarm in alarms
    ]


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
