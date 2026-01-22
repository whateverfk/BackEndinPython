from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_async_db as get_db
from app.api.deps import  get_current_user, CurrentUser
from app.features.sync.engine import SyncEngine
from app.Models.sync_setting import SyncSetting
from app.schemas.sync_setting import SyncSettingOut
from app.schemas.sync_setting import SyncSettingUpdate

router = APIRouter(prefix="/api/sync", tags=["Sync"])


@router.post("/now")
async def sync_now(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    engine = SyncEngine()
    await engine.sync_by_superadmin(db, user.superadmin_id)
    return {"message": "Sync started"}

# =========================
# GET: api/sync/setting
# =========================
@router.get("/setting", response_model=SyncSettingOut)
async def get_setting(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    result = await db.execute(
        select(SyncSetting)
        .where(SyncSetting.owner_superadmin_id == user.superadmin_id)
    )
    setting = result.scalars().first()

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
async def update_setting(
    dto: SyncSettingUpdate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    result = await db.execute(
        select(SyncSetting)
        .where(SyncSetting.owner_superadmin_id == user.superadmin_id)
    )
    setting = result.scalars().first()

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

    await db.commit()
    
    return {"message": "Saved"}