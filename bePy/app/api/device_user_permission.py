from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.features.deps import build_hik_auth
from app.db.session import get_db
from app.Models.device_user import DeviceUser
from app.Models.user_global_permissions import UserGlobalPermission
from app.Models.user_channel_permissions import UserChannelPermission
from app.features.GetDevicesDetail.HikDetailService import HikDetailService
from app.features.GetDevicesDetail.WorkWithDb import save_permissions
from app.Models.device import Device

router = APIRouter(  prefix="/api/device/{id}/user/{device_user_id}/permissions",
    tags=["Devices_user_info"])



def build_permission_response(db, device_user_id: int):
    result = {
        "local": {"global": {}, "channels": {}},
        "remote": {"global": {}, "channels": {}},
    }

    # GLOBAL
    globals_ = db.query(UserGlobalPermission).filter(
        UserGlobalPermission.device_user_id == device_user_id
    ).all()

    for g in globals_:
        result[g.scope]["global"] = {
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

    # CHANNEL
    channels = db.query(UserChannelPermission).filter(
        UserChannelPermission.device_user_id == device_user_id,
        UserChannelPermission.enabled == True
    ).all()

    for c in channels:
        result[c.scope]["channels"].setdefault(c.permission, []).append(c.channel_id)
    print(result)
    return result


@router.get("")
async def get_device_user_permissions(
    id: int,
    device_user_id: int,
    db: Session = Depends(get_db),
   
):
    permission_service=  HikDetailService()
    # 1. Check user
    device_user = db.query(DeviceUser).get(device_user_id)
    if not device_user:
        raise HTTPException(404, "Device user not found")

    # 2. Check permission exists?
    exists = db.query(UserGlobalPermission).filter(
        UserGlobalPermission.device_user_id == device_user_id
    ).first()

    # 3. If NOT exists → fetch from device
    if not exists:
        device = device_user.device
        headers = build_hik_auth(device)

        permission_data = await permission_service.fetch_permission_for_1_user(
            device=device,
            headers=headers,
            user_id=device_user.user_id
        )

        if not permission_data:
            raise HTTPException(500, "Failed to fetch permission from device")

        save_permissions(
            db=db,
            device_user_id=device_user_id,
            permission_data=permission_data
        )

    # 4. Build response from DB (bạn đã có sẵn)
    return build_permission_response(db, device_user_id)

@router.post("/sync")
async def sync_user_permission(
    id: int,
    device_user_id: int,
    db: Session = Depends(get_db),
):
    """
    Fetch permission từ device cho 1 user
    và upsert vào DB
    """
    device = db.get(Device, id)
    if not device:
        raise HTTPException(404, "Device not found")

    device_user = db.query(DeviceUser).filter_by(
        id=device_user_id,
        device_id=id
    ).first()

    if not device_user:
        raise HTTPException(404, "User not found")

    headers = build_hik_auth(device)
    hik = HikDetailService()

    permission_data = await hik.fetch_permission_for_1_user(
        device=device,
        headers=headers,
        user_id=device_user.user_id  # ISAPI user id
    )

    if not permission_data:
        raise HTTPException(502, "Cannot fetch permission from device")

    save_permissions(
        db=db,
        device_user_id=device_user.id,
        permission_data=permission_data
    )

    return {"status": "success"}
