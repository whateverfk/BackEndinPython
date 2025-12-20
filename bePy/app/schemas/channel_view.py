# app/schemas/channel_view.py
from pydantic import BaseModel
from typing import List

class TimeRangeView(BaseModel):
    start: str
    end: str

class ChannelView(BaseModel):
    id: int
    name: str
    time_ranges: List[TimeRangeView]

class DeviceChannelView(BaseModel):
    id: int
    ip: str
    username: str
    channels: List[ChannelView]
