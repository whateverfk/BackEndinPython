# app/schemas/sync_log.py
from pydantic import BaseModel
from datetime import datetime


class SyncLogOut(BaseModel):
    id: int
    device_id: int | None
    ip: str | None
    sync_time: datetime
    is_success: bool
    message: str

    class Config:
        from_attributes = True
