from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class AlarmItem(BaseModel):
    id: int
    device_id: Optional[int]
    message: str
    created_at: datetime


class AlarmPage(BaseModel):
    items: List[AlarmItem]
    next_cursor_time: Optional[datetime]
    next_cursor_id: Optional[int]
    has_more: bool
