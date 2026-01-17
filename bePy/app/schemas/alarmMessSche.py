from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class AlarmItem(BaseModel):
    id: int
    device_id: int | None
    event: str
    channel_id_in_device: str | None
    channel_name: str | None
    message: str
    created_at: datetime


class AlarmPage(BaseModel):
    items: list[AlarmItem]
    next_cursor_time: datetime | None
    next_cursor_id: int | None
    has_more: bool
