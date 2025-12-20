from datetime import datetime
from pydantic import BaseModel


class RecordTimeRange(BaseModel):
    start_time: datetime
    end_time: datetime


class ChannelRecordInfo(BaseModel):
    channel_id: int
    channel_name: str
    oldest_date: str | None
    time_ranges: list[RecordTimeRange]
