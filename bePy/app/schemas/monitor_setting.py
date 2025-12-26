from pydantic import BaseModel, Field


class MonitorSettingBase(BaseModel):
    start_day: int = Field(ge=1, le=31, default=1)
    end_day: int = Field(ge=1, le=31, default=31)
    order: bool = False


class MonitorSettingCreate(MonitorSettingBase):
    pass


class MonitorSettingOut(MonitorSettingBase):
    id: int

    class Config:
        from_attributes = True
