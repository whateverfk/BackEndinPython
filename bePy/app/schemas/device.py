from pydantic import BaseModel
from typing import Optional

class DeviceBase(BaseModel):
    ip_nvr: Optional[str] = None
    ip_web: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    brand: Optional[str] = None
    is_checked: bool = None


class DeviceCreate(DeviceBase):
    
    ip_nvr: str
    ip_web: str
    username: str
    password: str
    brand: str
    is_checked: bool = True



class DeviceUpdate(DeviceBase):
    pass


class DeviceOut(BaseModel):
    id: int
    ip_nvr: str
    ip_web: str
    username: str
    brand: str
    is_checked: bool

    class Config:
        from_attributes = True

