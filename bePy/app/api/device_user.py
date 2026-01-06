from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.Models.device import Device
from app.features.GetDevicesDetail.HikDetailService import HikDetailService
from app.features.GetDevicesDetail.WorkWithDb import (
    upsert_device_users,
    get_device_users_from_db
)
from app.features.deps import build_hik_auth


router = APIRouter(
    prefix="/api/device/{id}/user",
    tags=["Device_user"]
)


@router.post("/sync")
async def sync_device_users(
    id: int,
    db: Session = Depends(get_db),
    
):
    """
    Fetch user list từ ISAPI và upsert vào DB
    """
    device = db.get(Device,id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    headers = build_hik_auth(device)
    hik = HikDetailService()
    
    users = await hik.fetch_device_users(device, headers)

    if not users:
        raise HTTPException(
            status_code=502,
            detail="Cannot fetch users from device"
        )

    upsert_device_users(
        db=db,
        device_id=device.id,
        users_data=users
    )

    return {
        "status": "success",
        "count": len(users)
    }

@router.get("")
def get_device_users(
    id: int,
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách user của device từ DB
    """

    users = get_device_users_from_db(
        db=db,
        device_id=id
    )

    return users

