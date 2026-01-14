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
from fastapi import Body
from app.features.GetDevicesDetail.Change_permission import (
    create_user_permission_xml
)

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
    for ch in channels:
        scope = ch.scope          # local | remote
        perm = ch.permission      # playback | record | backup | ptz_control
        result[scope]["channels"].setdefault(perm, []).append(ch.channel_id)


   
    
    return result


@router.get("")
async def get_device_user_permissions(
    id: int,
    device_user_id: int,
    db: Session = Depends(get_db),
   
):
    permission_service=  HikDetailService()
    
    device_user = db.query(DeviceUser).get(device_user_id)
    if not device_user:
        raise HTTPException(404, "Device user not found")

   
    exists = db.query(UserGlobalPermission).filter(
        UserGlobalPermission.device_user_id == device_user_id
    ).first()

   
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

    # 4. Build response from DB 
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

@router.put("")
async def update_device_user_permissions(
    id: int,
    device_user_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
):
    """
    Update permission cho device user
    """

    # ===== 1. Validate device =====
    device = db.get(Device, id)
    if not device:
        raise HTTPException(404, "Device not found")

    # ===== 2. Validate device_user =====
    device_user = db.query(DeviceUser).filter_by(
        id=device_user_id,
        device_id=id
    ).first()

    if not device_user:
        raise HTTPException(404, "Device user not found")

    # ===== 3. Inject required IDs vào payload =====
    payload["device_id"] = id
    payload["device_user_id"] = device_user_id

    # ===== 4. Push permission lên thiết bị =====
    headers = build_hik_auth(device)
    hik = HikDetailService()

    
    result = await hik.put_permission(
            db=db,
            device=device,
            headers=headers,
            payload=payload
        )
    

    # ===== 5. Xử lý kết quả =====

    #  Thành công
    if result.get("success"):
        # sync lại DB nếu push OK
        permission_data = await hik.fetch_permission_for_1_user(
            device=device,
            headers=headers,
            user_id=device_user.user_id
        )

        if permission_data:
            save_permissions(
                db=db,
                device_user_id=device_user_id,
                permission_data=permission_data
            )

        return {
            "success": True,
            "code": "OK",
            "message": "Permission updated successfully"
        }


    #  Không đủ quyền
    if result.get("error") == "LOW_PRIVILEGE":
        return {
            "success": False,
            "code": "LOW_PRIVILEGE",
            "message": "Không đủ quyền để thay đổi permission trên thiết bị"
        }


    #  Thao tác không hợp lệ
    return {
        "success": False,
        "code": "INVALID_OPERATION",
        "message": "Thao tác không hợp lệ"
    }

