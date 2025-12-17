from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.Models.device import Device
from app.schemas.device import (
    DeviceCreate,
    DeviceUpdate,
    DeviceOut
)
from app.api.deps import get_db, get_current_user
from app.Models.user import User

router = APIRouter(
    prefix="/api/devices",
    tags=["Devices"]
)

# =========================
# GET: api/Devices
# =========================
@router.get("", response_model=list[DeviceOut])
def get_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Device).filter(
        Device.owner_superadmin_id == current_user.id
    ).all()


# =========================
# GET: api/Devices/{id}
# =========================
@router.get("/{id}", response_model=DeviceOut)
def get_device(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    device = db.query(Device).filter(
        Device.id == id,
        Device.owner_superadmin_id == current_user.id
    ).first()

    if not device:
        raise HTTPException(404)

    return device


# =========================
# POST: api/Devices
# =========================
@router.post("", response_model=DeviceOut, status_code=201)
def create_device(
    dto: DeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ip_web = dto.ip_web.strip() if dto.ip_web else None

    exists = db.query(Device).filter(
        Device.ip_web == ip_web,
        Device.owner_superadmin_id == current_user.id
    ).first()

    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Device with this IP Web already exists"
        )

    device = Device(
        ip_nvr=dto.ip_nvr,
        ip_web=ip_web,
        username=dto.username,
        password=dto.password,
        brand=dto.brand,
        is_checked=dto.is_checked,

        # 🔐 KHÔNG TIN CLIENT
        owner_superadmin_id=current_user.id
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    return device


# =========================
# PUT: api/Devices/{id}
# =========================
@router.put("/{id}", status_code=204)
def update_device(
    id: int,
    dto: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    device = db.query(Device).filter(
        Device.id == id,
        Device.owner_superadmin_id == current_user.id
    ).first()

    if not device:
        raise HTTPException(404)

    device.ip_nvr = dto.ip_nvr
    device.ip_web = dto.ip_web.strip() if dto.ip_web else None
    device.username = dto.username
    device.password = dto.password
    device.brand = dto.brand
    device.is_checked = dto.is_checked

    db.commit()
    return


# =========================
# DELETE: api/Devices/{id}
# =========================
@router.delete("/{id}", status_code=204)
def delete_device(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    device = db.query(Device).filter(
        Device.id == id,
        Device.owner_superadmin_id == current_user.id
    ).first()

    if not device:
        raise HTTPException(404)

    db.delete(device)
    db.commit()
    return
