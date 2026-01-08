from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.Models.monitor_setting import MonitorSetting
from app.schemas.monitor_setting import MonitorSettingOut, MonitorSettingCreate
from fastapi import HTTPException
from app.api.deps import get_db, get_current_user, CurrentUser

router = APIRouter(prefix="/api/config", tags=["Config"])



# =========================
# GET: api/sync/setting
# =========================
@router.get("", response_model=MonitorSettingOut)
def get_monitor_setting(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    setting = db.query(MonitorSetting).filter(
        MonitorSetting.owner_superadmin_id == user.superadmin_id
    ).first()

    if not setting:
        # trả default nếu chưa có
        setting = MonitorSetting(
            start_day=1,
            end_day=31,
            order=False,
            owner_superadmin_id=user.superadmin_id
        )
        db.add(setting)
        db.commit()
        db.refresh(setting)

    return setting

# =========================
# POST: api/sync/setting
# =========================

@router.post("", response_model=MonitorSettingOut)
def upsert_monitor_setting(
    dto: MonitorSettingCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    if dto.start_day > dto.end_day:
        raise HTTPException(
            status_code=400,
            detail="start_day <= end_day pls "
        )

    setting = db.query(MonitorSetting).filter(
        MonitorSetting.owner_superadmin_id == user.superadmin_id
    ).first()

    if setting:
        setting.start_day = dto.start_day
        setting.end_day = dto.end_day
        setting.order = dto.order
    else:
        setting = MonitorSetting(
            start_day=dto.start_day,
            end_day=dto.end_day,
            order=dto.order,
            owner_superadmin_id=user.superadmin_id
        )
        db.add(setting)

    db.commit()
    db.refresh(setting)
    return setting
