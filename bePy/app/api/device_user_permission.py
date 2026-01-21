from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_user, CurrentUser
from app.Models.device import Device
from app.Models.device_user import DeviceUser
from app.features.deps import build_hik_auth
from app.features.GetDevicesDetail.HikDetailService import HikDetailService
from app.features.GetDevicesDetail.WorkWithDb import save_permissions,sync_device_users_from_isapi
from app.utils.response_builders import build_permission_response
from app.services.device_service import get_device_or_404, get_device_user_or_404
from app.core.constants import ERROR_MSG_LOW_PRIVILEGE, ERROR_MSG_INVALID_OPERATION

router = APIRouter(
    prefix="/api/device/{id}/user",
    tags=["Devices_user_info"]
)


@router.get("/{device_user_id}/permissions")
async def get_device_user_permissions(
    id: int,
    device_user_id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """
    Get permissions for a specific device user.
    If permissions don't exist in DB, fetch from device.
    """
    device_user = get_device_user_or_404(db, device_user_id, id)
    device = device_user.device

    # Check if we already have permissions in DB (checking just one global permission record as proxy)
    from app.Models.user_global_permissions import UserGlobalPermission
    exists = db.query(UserGlobalPermission).filter(
        UserGlobalPermission.device_user_id == device_user_id
    ).first()

    if not exists:
        permission_service = HikDetailService()
        headers = build_hik_auth(device)

        permission_data = await permission_service.fetch_permission_for_1_user(
            device=device,
            headers=headers,
            user_id=device_user.user_id
        )

        if not permission_data:
            raise HTTPException(502, "Failed to fetch permission from device")

        save_permissions(
            db=db,
            device_user_id=device_user_id,
            permission_data=permission_data
        )

    return build_permission_response(db, device_user_id)


@router.post("/{device_user_id}/permissions/sync")
async def sync_user_permission(
    id: int,
    device_user_id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """
    Fetch and update permissions from device for a user.
    """
    device = get_device_or_404(db, id)
    device_user = get_device_user_or_404(db, device_user_id, id)

    headers = build_hik_auth(device)
    hik = HikDetailService()
    
    permission_data = await hik.fetch_permission_for_1_user(
        device=device,
        headers=headers,
        user_id=device_user.user_id
    )

    if not permission_data:
        raise HTTPException(502, "Cannot fetch permission from device")

    save_permissions(
        db=db,
        device_user_id=device_user.id,
        permission_data=permission_data
    )

    return {"status": "success"}


@router.put("/{device_user_id}/permissions")
async def update_device_user_permissions(
    id: int,
    device_user_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """
    Update permissions for a device user on both the device and DB.
    """
    device = get_device_or_404(db, id)
    device_user = get_device_user_or_404(db, device_user_id, id)

    # Inject required IDs into payload for the service
    payload["device_id"] = id
    payload["device_user_id"] = device_user_id

    headers = build_hik_auth(device)
    hik = HikDetailService()

    result = await hik.put_permission(
        db=db,
        device=device,
        headers=headers,
        payload=payload
    )

    if result.get("success"):
        # Sync back from device to ensure DB matches device state
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

    if result.get("error") == "LOW_PRIVILEGE":
        return {
            "success": False,
            "code": "LOW_PRIVILEGE",
            "message": ERROR_MSG_LOW_PRIVILEGE
        }

    return {
        "success": False,
        "code": "INVALID_OPERATION",
        "message": ERROR_MSG_INVALID_OPERATION
    }


@router.post("/syncall")
async def sync_all_device_user_permissions(
    id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    device = get_device_or_404(db, id)
    headers = build_hik_auth(device)

    # =========================
    # STEP 1: SYNC DEVICE USERS
    # =========================
    users = await sync_device_users_from_isapi(
        db=db,
        device=device,
        headers=headers
    )


    # =========================
    # STEP 2: LOAD USERS FROM DB
    # =========================
    device_users = (
        db.query(DeviceUser)
        .filter(DeviceUser.device_id == id)
        .all()
    )

    if not device_users:
        return {
            "success": True,
            "message": "No device users found after sync",
            "total": 0,
            "synced": 0,
            "errors": []
        }

    # =========================
    # STEP 3: SYNC PERMISSIONS
    # =========================
    hik = HikDetailService()
    success_count = 0
    errors = []

    for device_user in device_users:
        try:
            permission_data = await hik.fetch_permission_for_1_user(
                device=device,
                headers=headers,
                user_id=device_user.user_id
            )

            if not permission_data:
                errors.append({
                    "device_user_id": device_user.id,
                    "user_id": device_user.user_id,
                    "error": "FETCH_FAILED"
                })
                continue

            save_permissions(
                db=db,
                device_user_id=device_user.id,
                permission_data=permission_data
            )

            success_count += 1

        except Exception as e:
            errors.append({
                "device_user_id": device_user.id,
                "user_id": device_user.user_id,
                "error": str(e)
            })

    db.commit()

    return {
        "success": True,
        "device_id": id,
        "total": len(device_users),
        "synced": success_count,
        "failed": len(errors),
        "errors": errors
    }
