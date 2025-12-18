from pydantic import BaseModel


class SyncSettingBase(BaseModel):
    is_enabled: bool
    interval_minutes: int


class SyncSettingOut(SyncSettingBase):
    class Config:
        from_attributes = True

class SyncSettingUpdate(BaseModel):
    is_enabled: bool
    interval_minutes: int

