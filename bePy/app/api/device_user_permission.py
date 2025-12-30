from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.Models.device_user import DeviceUser
from app.Models.user_global_permissions import UserGlobalPermission
from app.features.GetDevicesDetail.PermissionMap import PERMISSION_LABELS
from app.Models.user_channel_permissions import UserChannelPermission

router = APIRouter(  prefix="/api/device/{id}/user/{device_user_id}",
    tags=["Devices_user_info"])


@router.get("/permissions")
def get_device_user_permissions(
    device_user_id: int,
    db: Session = Depends(get_db)
):
    device_user = db.query(DeviceUser).get(device_user_id)
    if not device_user:
        raise HTTPException(404, "Device user not found")

    result = {
        "local": {"global": {}, "channels": {}},
        "remote": {"global": {}, "channels": {}}
    }

    # ========== GLOBAL ==========
    globals_ = db.query(UserGlobalPermission).filter(
        UserGlobalPermission.device_user_id == device_user_id
    ).all()

    for g in globals_:
        scope = g.scope

        result[scope]["global"] = {
            "upgrade": g.upgrade,
            "parameter_config": g.parameter_config,
            "restart_or_shutdown": g.restart_or_shutdown,
            "log_or_state_check": g.log_or_state_check,
            "manage_channel": g.manage_channel,

            "playback": g.playback,
            "record": g.record,
            "backup": g.backup,

            "preview": g.preview,
            "voice_talk": g.voice_talk,
            "alarm_out_or_upload": g.alarm_out_or_upload,
            "control_local_out": g.control_local_out,
            "transparent_channel": g.transparent_channel,
        }

    # ========== CHANNEL ==========
    channels = db.query(UserChannelPermission).filter(
        UserChannelPermission.device_user_id == device_user_id,
        UserChannelPermission.enabled == True
    ).all()

    for c in channels:
        scope = c.scope
        perm = c.permission

        result[scope]["channels"].setdefault(perm, [])
        result[scope]["channels"][perm].append(c.channel_id)

    return result
