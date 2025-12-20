from abc import ABC, abstractmethod
from typing import List
from app.schemas.record import ChannelRecordInfo


class RecordService(ABC):

    @abstractmethod
    async def get_channels_record_info(
        self,
        device
    ) -> List[ChannelRecordInfo]:
        """
        Trả về danh sách channel + thông tin record (oldest date, time range)
        """
        pass
