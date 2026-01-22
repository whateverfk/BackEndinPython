
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.Models.user_global_permissions import UserGlobalPermission
from app.Models.user_channel_permissions import UserChannelPermission


async def build_permission_response(db: AsyncSession, device_user_id: int) -> Dict[str, Any]:
    
    result = {
        "local": {"global": {}, "channels": {}},
        "remote": {"global": {}, "channels": {}},
    }

    # 1. GLOBAL PERMISSIONS
    stmt_result = await db.execute(
        select(UserGlobalPermission)
        .where(UserGlobalPermission.device_user_id == device_user_id)
    )
    globals_query = stmt_result.scalars().all()

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
    stmt_result = await db.execute(
        select(UserChannelPermission)
        .where(
            UserChannelPermission.device_user_id == device_user_id,
            UserChannelPermission.enabled == True
        )
    )
    channels_query = stmt_result.scalars().all()
    
    for ch in channels_query:
        scope = ch.scope          # local | remote
        perm = ch.permission      # playback | record | backup | ptz_control
        result[scope]["channels"].setdefault(perm, []).append(ch.channel_id)

    return result
