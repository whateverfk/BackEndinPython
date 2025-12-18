from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, CurrentUser
from app.Models.device import Device
from app.schemas.device import (
    DeviceCreate,
    DeviceUpdate,
    DeviceOut
)

router = APIRouter(
    prefix="/api/devices",
    tags=["Devices"]
)

# =========================
# GET: /api/devices
# =========================
@router.get("", response_model=list[DeviceOut])
def get_devices(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    return db.query(Device).filter(
        Device.owner_superadmin_id == user.superadmin_id
    ).all()


# =========================
# POST: /api/devices
# =========================
@router.post("", response_model=DeviceOut, status_code=status.HTTP_201_CREATED)
def create_device(
    dto: DeviceCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    exists = db.query(Device).filter(
        Device.ip_web == dto.ip_web,
        Device.owner_superadmin_id == user.superadmin_id
    ).first()
    print("DTO RECEIVED:", dto.model_dump())

    if exists:
        raise HTTPException(status_code=409, detail="Device already exists")

    device = Device(
        ip_web=dto.ip_web,
        ip_nvr=dto.ip_nvr,
        username=dto.username,
        password=dto.password,
        brand=dto.brand,
        is_checked=dto.is_checked,
        owner_superadmin_id=user.superadmin_id
    )

    db.add(device)
    db.commit()
    db.refresh(device)
    return device


# =========================
# PUT: /api/devices/{id}
# =========================
@router.put("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def update_device(
    id: int,
    dto: DeviceUpdate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    device = db.query(Device).filter(
        Device.id == id,
        Device.owner_superadmin_id == user.superadmin_id
    ).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device.ip_web = dto.ip_web
    device.ip_nvr = dto.ip_nvr
    device.username = dto.username
    device.password = dto.password
    device.brand = dto.brand
    device.is_checked = dto.is_checked

    db.commit()
    return


# =========================
# DELETE: /api/devices/{id}
# =========================
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(
    id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    device = db.query(Device).filter(
        Device.id == id,
        Device.owner_superadmin_id == user.superadmin_id
    ).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    db.delete(device)
    db.commit()
    return

@router.get("/{id}", response_model=DeviceOut)
def get_device(
    id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user)
):
    device = db.query(Device).filter(
        Device.id == id,
        Device.owner_superadmin_id == user.superadmin_id
    ).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    return device
