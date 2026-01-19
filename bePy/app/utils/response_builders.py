
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.Models.user_global_permissions import UserGlobalPermission
from app.Models.user_channel_permissions import UserChannelPermission


def build_permission_response(db: Session, device_user_id: int) -> Dict[str, Any]:
    
    result = {
        "local": {"global": {}, "channels": {}},
        "remote": {"global": {}, "channels": {}},
    }

    # 1. GLOBAL PERMISSIONS
    globals_query = db.query(UserGlobalPermission).filter(
        UserGlobalPermission.device_user_id == device_user_id
    ).all()

    for g in globals_query:
        result[g.scope]["global"] = {
            "upgrade": g.upgrade,
            "parameter_config": g.parameter_config,
            "restart_or_shutdown": g.restart_or_shutdown,
            "log_or_state_check": g.log_or_state_check,
            "manage_channel": g.manage_channel,

            "playback": g.playback,
            "record": g.record,
            "backup": g.backup,
            "ptz_control":g.ptz_control,

            "preview": g.preview,
            "voice_talk": g.voice_talk,
            "alarm_out_or_upload": g.alarm_out_or_upload,
            "control_local_out": g.control_local_out,
            "transparent_channel": g.transparent_channel,
        }

    # 2. CHANNEL PERMISSIONS
    channels_query = db.query(UserChannelPermission).filter(
        UserChannelPermission.device_user_id == device_user_id,
        UserChannelPermission.enabled == True
    ).all()
    
    for ch in channels_query:
        scope = ch.scope          # local | remote
        perm = ch.permission      # playback | record | backup | ptz_control
        result[scope]["channels"].setdefault(perm, []).append(ch.channel_id)

    return result
