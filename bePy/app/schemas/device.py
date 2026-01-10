from pydantic import BaseModel
from typing import Optional

class DeviceBase(BaseModel):
    ip_nvr: Optional[str] = None
    ip_web: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    brand: Optional[str] = None
    is_checked: bool = True


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(DeviceBase):
    pass


class DeviceOut(DeviceBase):
    id: int

    class Config:
        from_attributes = True
