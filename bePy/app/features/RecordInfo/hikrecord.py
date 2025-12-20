import httpx
from datetime import datetime
from typing import List

from app.schemas.record import (
    ChannelRecordInfo,
    RecordTimeRange
)
from app.features.RecordInfo.base import RecordService
from app.features.RecordInfo.deps import build_hik_auth


class HikvisionRecordService(RecordService):

    async def _get_channels(self, device, headers):
        """
        MOCK channel list
        Sau này thay bằng parse XML thật
        """
        return [
            {"id": 101, "name": "Camera 1"},
            {"id": 201, "name": "Camera 2"},
        ]

    async def _mock_oldest_record_date(
        self,
        device,
        channel_id: int
    ) -> str | None:
        """
        MOCK oldest record date
        Sau này thay bằng dailyDistribution
        """
        return "2024-07-18"

    async def _mock_time_ranges(
        self,
        date_str: str
    ) -> list[RecordTimeRange]:
        """
        MOCK time ranges – phản ánh tình huống mất điện, mất mạng
        """
        return [
            RecordTimeRange(
                start_time=datetime.fromisoformat(
                    f"{date_str}T00:15:00"
                ),
                end_time=datetime.fromisoformat(
                    f"{date_str}T02:40:00"
                ),
            ),
            RecordTimeRange(
                start_time=datetime.fromisoformat(
                    f"{date_str}T03:10:00"
                ),
                end_time=datetime.fromisoformat(
                    f"{date_str}T06:00:00"
                ),
            ),
        ]

    async def get_channels_record_info(
        self,
        device
    ) -> List[ChannelRecordInfo]:

        headers = build_hik_auth(device)

        channels = await self._get_channels(device, headers)

        result: List[ChannelRecordInfo] = []

        for ch in channels:
            oldest_date = await self._mock_oldest_record_date(
                device,
                ch["id"]
            )

            if oldest_date:
                time_ranges = await self._mock_time_ranges(
                    oldest_date
                )
            else:
                time_ranges = []

            result.append(
                ChannelRecordInfo(
                    channel_id=ch["id"],
                    channel_name=ch["name"],
                    oldest_date=oldest_date,
                    time_ranges=time_ranges
                )
            )

        return result
