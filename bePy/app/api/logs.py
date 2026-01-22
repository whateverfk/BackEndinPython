from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime, timedelta, timezone
from app.api.deps import  get_current_user, CurrentUser
from app.db.session import get_async_db as get_db
from app.Models.sync_log import SyncLog
from app.schemas.sync_log import SyncLogOut
from app.schemas.log_search import DeviceLogRequest
from app.Models.device import Device
from app.features.Log_device.log_device import fetch_isapi_logs
from app.features.deps import build_hik_auth
from app.services.device_service import get_device_or_404
from app.core.constants import ERROR_MSG_DEVICE_NOT_FOUND

router = APIRouter(
    prefix="/api/logs",
    tags=["Logs"]
)

# =========================
# GET: api/logs
# =========================
@router.get("", response_model=list[SyncLogOut])
async def get_logs(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    await cleanup_old_logs(db)
    result = await db.execute(
        select(SyncLog)
        .where(SyncLog.owner_superadmin_id == user.superadmin_id)
        .order_by(SyncLog.sync_time.desc())
        .limit(200)
    )
    logs = result.scalars().all()

    return logs

async def cleanup_old_logs(db: AsyncSession):
    cutoff = datetime.now() - timedelta(days=7)

    await db.execute(
        delete(SyncLog).where(
            SyncLog.sync_time < cutoff
        )
    )
    await db.commit()

@router.post("/device/{device_id}")
async def get_device_logs(
    device_id: int,
    body: DeviceLogRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """
    Fetch device logs via Hikvision ISAPI
    """

    # ---- get device ----
    device = await get_device_or_404(db, device_id)

    # ---- build auth headers ----
    try:
        headers = build_hik_auth(device)
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build device auth headers: {ex}"
        )

    # ---- validate input ----
    if body.maxResults < 1 or body.maxResults > 2000:
        body.maxResults = 2000

    # ---- call ISAPI ----
    data = await fetch_isapi_logs(
        device=device,
        headers=headers,
        from_time=body.from_,
        to_time=body.to,
        max_results=body.maxResults,
        major_type=body.majorType
    )

    if data is None:
        raise HTTPException(
            status_code=502,
            detail="Failed to fetch logs from device"
        )

    return data
