# app/schemas/channel_record.py
from pydantic import BaseModel
from datetime import date, datetime
from typing import List

class ChannelRecordTimeRangeOut(BaseModel):
    start_time: datetime
    end_time: datetime

    class Config:
        from_attributes = True


class ChannelRecordDayOut(BaseModel):
    record_date: date
    has_record: bool
    time_ranges: List[ChannelRecordTimeRangeOut]

    class Config:
        from_attributes = True
