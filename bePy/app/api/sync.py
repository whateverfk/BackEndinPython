from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, CurrentUser
from app.sync.engine import SyncEngine
from app.Models.sync_setting import SyncSetting
from app.schemas.sync_setting import SyncSettingOut
from app.schemas.sync_setting import SyncSettingUpdate

router = APIRouter(prefix="/api/sync", tags=["Sync"])


@router.post("/now")
async def sync_now(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    engine = SyncEngine()
    await engine.sync_by_superadmin(db, user.superadmin_id)
    return {"message": "Sync started"}

# =========================
# GET: api/sync/setting
# =========================
@router.get("/setting", response_model=SyncSettingOut)
def get_setting(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    setting = db.query(SyncSetting).filter(
        SyncSetting.owner_superadmin_id == user.superadmin_id
    ).first()

    if not setting:
        return SyncSettingOut(
            is_enabled=False,
            interval_minutes=60
        )

    return setting


# =========================
# POST: api/sync/setting
# =========================
@router.post("/setting")
def update_setting(
    dto: SyncSettingUpdate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    setting = db.query(SyncSetting).filter(
        SyncSetting.owner_superadmin_id == user.superadmin_id
    ).first()

    if not setting:
        setting = SyncSetting(
            is_enabled=dto.is_enabled,
            interval_minutes=dto.interval_minutes,
            owner_superadmin_id=user.superadmin_id
        )
        db.add(setting)
    else:
        setting.is_enabled = dto.is_enabled
        setting.interval_minutes = dto.interval_minutes

    db.commit()
    return {"message": "Saved"}