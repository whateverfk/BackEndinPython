from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.api.deps import get_db, get_current_user, CurrentUser
from app.Models.sync_log import SyncLog
from app.schemas.sync_log import SyncLogOut

router = APIRouter(
    prefix="/api/logs",
    tags=["Logs"]
)

# =========================
# GET: api/logs
# =========================
@router.get("", response_model=list[SyncLogOut])
def get_logs(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    cleanup_old_logs(db)
    logs = (
        db.query(SyncLog)
        .filter(SyncLog.owner_superadmin_id == user.superadmin_id)
        .order_by(SyncLog.sync_time.desc())
        .limit(200)
        .all()
    )

    return logs

def cleanup_old_logs(db: Session):
    cutoff = datetime.now().astimezone() - timedelta(days=7)

    db.query(SyncLog).filter(
        SyncLog.sync_time < cutoff
    ).delete(synchronize_session=False)
    db.commit()