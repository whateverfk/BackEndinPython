from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_user, CurrentUser
from app.Models.device import Device
from app.Models.device_user import DeviceUser
from app.features.deps import build_hik_auth
from app.features.GetDevicesDetail.HikDetailService import HikDetailService
from app.features.GetDevicesDetail.WorkWithDb import save_permissions
from app.utils.response_builders import build_permission_response
from app.services.device_service import get_device_or_404, get_device_user_or_404
from app.core.constants import ERROR_MSG_LOW_PRIVILEGE, ERROR_MSG_INVALID_OPERATION

router = APIRouter(
    prefix="/api/device/{id}/user/{device_user_id}/permissions",
    tags=["Devices_user_info"]
)


@router.get("")
async def get_device_user_permissions(
    id: int,
    device_user_id: int,
    db: Session = Depends(get_db),
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


@router.post("/sync")
async def sync_user_permission(
    id: int,
    device_user_id: int,
    db: Session = Depends(get_db),
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


@router.put("")
async def update_device_user_permissions(
    id: int,
    device_user_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
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


