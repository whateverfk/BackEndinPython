from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_async_db as get_db
from app.api.deps import get_current_user, CurrentUser
from app.Models.monitor_setting import MonitorSetting
from app.schemas.monitor_setting import MonitorSettingOut, MonitorSettingCreate

router = APIRouter(prefix="/api/config", tags=["Config"])



# =========================
# GET: api/sync/setting
# =========================
@router.get("", response_model=MonitorSettingOut)
async def get_monitor_setting(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    result = await db.execute(
        select(MonitorSetting)
        .where(MonitorSetting.owner_superadmin_id == user.superadmin_id)
    )
    setting = result.scalars().first()

    if not setting:
        # trả default nếu chưa có
        setting = MonitorSetting(
            start_day=1,
            end_day=31,
            order=False,
            owner_superadmin_id=user.superadmin_id
        )
        db.add(setting)
        await db.commit()
        await db.refresh(setting)

    return setting

# =========================
# POST: api/sync/setting
# =========================

@router.post("", response_model=MonitorSettingOut)
async def upsert_monitor_setting(
    dto: MonitorSettingCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    if dto.start_day > dto.end_day:
        raise HTTPException(
            status_code=400,
            detail="start_day <= end_day pls "
        )

    result = await db.execute(
        select(MonitorSetting)
        .where(MonitorSetting.owner_superadmin_id == user.superadmin_id)
    )
    setting = result.scalars().first()

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

    await db.commit()
    await db.refresh(setting)
    return setting
